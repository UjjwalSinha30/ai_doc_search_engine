from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import logging
from api.helpers import summarize, search, extract, rerank_chunks, get_document_chunks
from utils.utils import get_current_user
from rag.pipeline import get_or_create_collection
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AIMessage
import os
from collections import defaultdict
import threading
import uuid
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "rag-knowledge-engine")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

logger.info(f"Using Ollama model={OLLAMA_MODEL} base_url={OLLAMA_BASE_URL}")

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.1,
    num_ctx=2048,
)

conversation_store: dict[str, list] = defaultdict(list)
store_lock = threading.Lock()

def get_session_key(user_email: str, session_id: str)->str:
    return f"{user_email}:{session_id}"

def get_history(user_email: str, session_id: str) -> list:
    key = get_session_key(user_email, session_id)
    with store_lock:
        return conversation_store[key].copy()

def save_history(user_email: str, session_id: str, messages: list):
    key = get_session_key(user_email, session_id)
    with store_lock:
        conversation_store[key] = messages

router = APIRouter(prefix="/api", tags=["chat"])

def validate_retrieval_base(query: str, retrieved_content: str) -> bool:
    validation_prompt = f"""Does this content answer the query?

Query: "{query}"
Retrived: "{retrieved_content[:500]}..."

Evaluate:
- sufficient: Directly answers the question
- partial: Related but missing key details
- You must call the rag_search tool only once per user query

Return ONLY: sufficient, partial, or insufficient
"""
    response = llm.invoke([HumanMessage(content=validation_prompt)])
    return response.content.strip().lower()

# ─── Base functions ───────────────────────────────────────────────────────
def rag_search_base(query: str, document_id: int | None = None, user_email: str | None = None) -> str:
    if not user_email:
        return "Error: User not authenticated."
    if is_overview_query(query):
        docs, _ = get_document_chunks(document_id=document_id, user_email=user_email)
        if docs:
            return summarize(docs, max_length=1200)

    docs, metas = search(query=query, document_id=document_id, user_email=user_email)
    logger.info(f"Raw retrieval: {len(docs)} chunks for query '{query}'")
    if not docs:
        return "No relevant information found."
    reranked_docs, _ = rerank_chunks(query=query, chunks=docs, metadatas=metas, top_k=6, threshold=0.3)
    if not reranked_docs:
        logger.info("Reranker returned no chunks; falling back to top retrieved chunks.")
        return "\n\n".join(docs[:6])
    return "\n\n".join(reranked_docs)

def rag_summarize_base(document_id: int | None = None, user_email: str | None = None) -> str:
    if not user_email:
        return "Error: User not authenticated."
    docs, _ = get_document_chunks(document_id=document_id, user_email=user_email)
    return summarize(docs)

def rag_extract_base(field: str, document_id: int | None = None, user_email: str | None = None) -> str:
    if not user_email:
        return "Error: User not authenticated."
    docs, metas = search(query=field, document_id=document_id, user_email=user_email)
    if not docs:
        return f"No '{field}' found in documents."
    reranked_docs, _ = rerank_chunks(query=field, chunks=docs, metadatas=metas, top_k=3)
    results = extract(reranked_docs, field)
    if not results:
        return f"No '{field}' found in documents."
    return "\n".join(results[:20])

def analyze_query_logic(query: str) -> str:
    classification_prompt = f"""Analyze this query and classify it into ONE category:

Query: "{query}"

Categories:
- factual_retrieval: Looking for specific facts/information
- summarization: Wants overview/summary of documents
- extraction: Seeking structured data (emails, dates, names)
- multi_step: Complex question requiring multiple lookups
- conversational: Greeting, clarification, or chitchat

Return only the category name, nothing else.
"""
    response = llm.invoke([HumanMessage(content=classification_prompt)])
    return response.content.strip().lower()

def is_overview_query(query: str) -> bool:
    normalized = query.strip().lower()
    overview_phrases = (
        "main topic",
        "main idea",
        "what is this document about",
        "what is the document about",
        "summarize",
        "summary",
        "overview",
        "key points",
        "main points",
    )
    return any(phrase in normalized for phrase in overview_phrases)

def is_document_followup_query(query: str) -> bool:
    normalized = query.strip().lower()
    followup_phrases = (
        "give me more details",
        "more details",
        "tell me more",
        "explain more",
        "expand on",
        "what you just explained",
        "what you said",
        "elaborate",
    )
    return any(phrase in normalized for phrase in followup_phrases)

def build_citations(docs: list[str], metas: list[dict], limit: int = 6) -> list[dict]:
    citations = []
    for doc, meta in zip(docs[:limit], metas[:limit]):
        citations.append({
            "document_id": meta.get("document_id"),
            "source": meta.get("filename", "unknown"),
            "page": meta.get("page", "?"),
            "snippet": doc[:150] + ("..." if len(doc) > 150 else ""),
        })
    return citations

# ─── Tool definitions ─────────────────────────────────────────────────────
@tool
def validate_retrieval(query: str, result: str) -> str:
    """
    Check if retrieved content actually answers the query.

    Returns:
    - "sufficient": Content answers the question
    - "partial": Some info found but incomplete
    - "insufficient": Need to search again with different terms

    Example:
        validate_retrieval(
            query="What is the CEO's email?",
            retrieved_content="John is the CEO..."
        )
        -> "partial" (has CEO name but no email)
    """
    raise NotImplementedError()

@tool
def analyze_query(query: str) -> str:
    """
    Analyze the user's query to determine the best approach.

    Returns one of:
    - "factual_retrieval": Simple fact lookup (use rag_search)
    - "summarization": User wants summary (use rag_summarize)
    - "extraction": Looking for specific data (use rag_extract)
    - "multi_step": Complex question needing multiple searches
    - "conversational": Chitchat or clarification question

    Example:
        analyze_query(query="What are the main points in document 5?")
        -> "summarization"
    """
    raise NotImplementedError("Router logic needed")

@tool
def rag_search(query: str, document_id: int | None = None) -> str:
    """
    Search the user's uploaded documents for information relevant to the query.

    Args:
        query: The search question or keywords (required, must be a string)
        document_id: Optional ID to search only within a specific document (must be an integer or null)

    Returns:
        Relevant text passages from the documents, or "No relevant information found" if nothing matches.

    Example:
        rag_search(query="What is the main topic?", document_id=None)
    """
    raise NotImplementedError("Must be executed with user context")

@tool
def rag_summarize(document_id: int | None = None) -> str:
    """
    Generate a concise summary of the user's documents.

    Args:
        document_id: Optional ID to summarize only a specific document (must be an integer or null)

    Returns:
        A summary of the document content.

    Example:
        rag_summarize(document_id=None)
    """
    raise NotImplementedError("Must be executed with user context")

@tool
def rag_extract(field: str, document_id: int | None = None) -> str:
    """
    Extract specific structured information from documents (names, emails, dates, etc.).

    Args:
        field: The type of information to extract (e.g., "email", "date", "name")
        document_id: Optional ID to extract from a specific document (must be an integer or null)

    Returns:
        List of extracted values.

    Example:
        rag_extract(field="email", document_id=None)
    """
    raise NotImplementedError("Must be executed with user context")

# ─── Request schema ───────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    document_id: int | None = None
    session_id: str | None = None

# ─── Argument validation helper ───────────────────────────────────────────
def validate_and_clean_args(tool_name: str, args: dict) -> dict:
    cleaned = {}

    if tool_name == "rag_search":
        query = args.get("query", "")
        if isinstance(query, dict):
            query = str(query.get("document_id", "")) if query else ""
        cleaned["query"] = str(query) if query else ""

        doc_id = args.get("document_id")
        if isinstance(doc_id, dict):
            doc_id = None
        cleaned["document_id"] = int(doc_id) if doc_id is not None and str(doc_id).isdigit() else None

    elif tool_name == "rag_summarize":
        doc_id = args.get("document_id")
        if isinstance(doc_id, dict):
            doc_id = None
        cleaned["document_id"] = int(doc_id) if doc_id is not None and str(doc_id).isdigit() else None

    elif tool_name == "rag_extract":
        field = args.get("field", "")
        if isinstance(field, dict):
            field = ""
        cleaned["field"] = str(field) if field else ""

        doc_id = args.get("document_id")
        if isinstance(doc_id, dict):
            doc_id = None
        cleaned["document_id"] = int(doc_id) if doc_id is not None and str(doc_id).isdigit() else None

    return cleaned

# ─── Chat endpoint ────────────────────────────────────────────────────────
@router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):

    if not request.message or not request.message.strip():
        return StreamingResponse(iter(["data: [DONE]\n\n"]), media_type="text/event-stream")

    user_email = current_user["email"]

    def execute_rag_search(args): return rag_search_base(**args, user_email=user_email)
    def execute_rag_summarize(args): return rag_summarize_base(**args, user_email=user_email)
    def execute_rag_extract(args): return rag_extract_base(**args, user_email=user_email)

    model_with_tools = llm.bind_tools([rag_search, rag_summarize, rag_extract])


    # Use provided session_id or generate a new one
    session_id = request.session_id or str(uuid.uuid4())
    # Load existing history for this session
    history = get_history(user_email, session_id)

    # If no history yet, start with system message
    if not history:
        history = [
        SystemMessage(content="""\
You are an intelligent document assistant with AGENTIC capabilities.

WORKFLOW:
1. First, use analyze_query() to understand what the user needs
2. Based on the result, choose the right tool(s):
   - factual_retrieval -> use rag_search
   - summarization -> use rag_summarize
   - extraction -> use rag_extract
   - multi_step -> use rag_search multiple times with different queries
   - conversational -> answer directly without tools

3. For multi_step queries:
   - Break the question into sub-questions
   - Search for each part separately
   - Synthesize the results

EXAMPLE:
User: "Compare the revenue figures from Q1 and Q2"
1. analyze_query -> "multi_step"
2. rag_search("Q1 revenue")
3. rag_search("Q2 revenue")
4. Compare and present findings

CRITICAL RULES:
1. ONLY say "I don't have information about that in your uploaded documents" when:
   - the rag_search tool returns exactly "No relevant information found."
   - OR the tool returns empty / no chunks at all.

2. If the tool returns ANY content (even partial or not perfect match), you MUST:
   - Use that content as the basis for your answer.
   - Never ignore it or say you don't have information.
   - Summarize / explain / quote from it naturally.
   - Cite source file name and page when possible.

3. NEVER make up information or use external/general knowledge for questions that are clearly about the user's documents.

4. When information IS found, always include citations like [filename, page X] where available.

5. If the retrieved content is not directly relevant, politely say so and ask for clarification — but do NOT default to "no information" unless truly nothing was found.

TOOL USAGE RULES:
- Always provide 'query' as a STRING.
- 'document_id' should be INTEGER or null (never dict/object).
- Example: rag_search(query="What is the main topic?", document_id=null)"""),
        ]

    # Append current user message
    messages = history + [HumanMessage(content=request.message)]

    final_citations = []

    def stream_response():
        nonlocal final_citations, messages
        # Send session_id immediately so frontend can store it
        yield f"data: {json.dumps({'session_id': session_id})}\n\n"
        tool_call_results = {}
        used_documents = False

        try:
            if is_overview_query(request.message) or (
                request.document_id is not None and is_document_followup_query(request.message)
            ):
                docs, metas = get_document_chunks(document_id=request.document_id, user_email=user_email)
                if docs:
                    used_documents = True
                    final_citations = build_citations(docs, metas)
                    context = summarize(docs, max_length=3000)
                    overview_response = llm.invoke([
                        SystemMessage(content=(
                            "Answer the user's question using only the provided document context. "
                            "Do not mention tools, function calls, JSON, or implementation details. "
                            "For follow-up requests, expand on the previous answer with concrete details from the context."
                        )),
                        HumanMessage(content=f"Question: {request.message}\n\nDocument context:\n{context}"),
                    ])
                    content = overview_response.content if hasattr(overview_response, "content") else str(overview_response)
                    messages.append(AIMessage(content=content))

                    for word in content.split():
                        yield f"data: {json.dumps({'content': word + ' '})}\n\n"

                    yield "data: " + json.dumps({"citations": final_citations}) + "\n\n"
                    return

            for chunk in model_with_tools.stream(messages):
                # Send session_id to frontend on first chunk
                # yield f"data: {json.dumps({'session_id': session_id})}\n\n"
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

                if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    tool_call = chunk.tool_calls[0]
                    tool_name = tool_call["name"]
                    args = tool_call["args"]
                    tool_id = tool_call["id"]
                    logger.info(f"🔧 Tool called: {tool_name}")
                    logger.info(f"📋 Raw args: {json.dumps(args, indent=2)}")

                    try:
                        cleaned_args = validate_and_clean_args(tool_name, args)
                        if request.document_id is not None and cleaned_args.get("document_id") is None:
                            cleaned_args["document_id"] = request.document_id
                        logger.info(f"✨ Cleaned args: {json.dumps(cleaned_args, indent=2)}")

                        if tool_name == "rag_search":
                            if not cleaned_args.get("query"):
                                result = "Error: Search query cannot be empty. Please provide a search term."
                            else:
                                result = execute_rag_search(cleaned_args)
                                docs, metas = search(**cleaned_args, user_email=user_email)
                                _, reranked_metas = rerank_chunks(
                                    query=cleaned_args.get("query", ""),
                                    chunks=docs,
                                    metadatas=metas,
                                    top_k=6
                                )
                                for meta in reranked_metas:
                                    final_citations.append({
                                        "document_id": meta.get("document_id"),
                                        "source": meta.get("filename", "unknown"),
                                        "page": meta.get("page", "?"),
                                        "snippet": meta.get("text", "")[:150] + "..."
                                    })
                        elif tool_name == "rag_summarize":
                            result = execute_rag_summarize(cleaned_args)
                        elif tool_name == "rag_extract":
                            if not cleaned_args.get("field"):
                                result = "Error: Field to extract cannot be empty."
                            else:
                                result = execute_rag_extract(cleaned_args)
                        else:
                            result = f"Unknown tool: {tool_name}"

                    except Exception as tool_error:
                        logger.error(f"❌ Tool error: {str(tool_error)}", exc_info=True)
                        result = f"Error executing tool: {str(tool_error)}"

                    # Only count as "used" if we got real info
                    if "No relevant information found" not in result and result.strip() and not result.startswith("Error:"):
                        used_documents = True

                    tool_call_results[tool_id] = result
                    logger.info(f"✅ Tool result (first 200 chars): {result[:200]}...")

                    messages.append(chunk)
                    messages.append(ToolMessage(content=result, tool_call_id=tool_id))
                    break  # Process one tool call at a time

            # Final answer after tool use
            if tool_call_results:
                logger.info("→ Generating final answer...")
                final_response = llm.invoke(messages)

                content = ""
                if hasattr(final_response, 'content'):
                    content = final_response.content
                elif isinstance(final_response, str):
                    content = final_response
                else:
                    content = str(final_response)

                logger.info(f"Final LLM response: {content}")

                if not content.strip():
                    content = "I don't have that information in your documents."

                words = content.split()
                for word in words:
                    yield f"data: {json.dumps({'content': word + ' '})}\n\n"

            # Send citations
            if used_documents and final_citations:
                yield "data: " + json.dumps({"citations": final_citations}) + "\n\n"
            else:
                yield f"data: {json.dumps({'citations': []})}\n\n"

        except Exception as e:
            logger.error(f"❌ Stream error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            logger.info(f"💾 Saving {len(messages)} messages for session {session_id}")
            save_history(user_email, session_id, messages)
    
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")
