from collections import defaultdict
import json
import logging
import os
import threading
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from api.helpers import extract, get_document_chunks, rerank_chunks, search, summarize
from utils.utils import get_current_user


LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING") or os.getenv("LANGCHAIN_TRACING_V2", "false")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT", "rag-knowledge-engine")

os.environ["LANGSMITH_TRACING"] = LANGSMITH_TRACING
os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
os.environ["LANGCHAIN_TRACING_V2"] = LANGSMITH_TRACING
os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

logger.info("Using Ollama model=%s base_url=%s", OLLAMA_MODEL, OLLAMA_BASE_URL)

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.1,
    num_ctx=2048,
)

conversation_store: dict[str, list] = defaultdict(list)
store_lock = threading.Lock()
router = APIRouter(prefix="/api", tags=["chat"])


def get_session_key(user_email: str, session_id: str) -> str:
    return f"{user_email}:{session_id}"


def get_history(user_email: str, session_id: str) -> list:
    key = get_session_key(user_email, session_id)
    with store_lock:
        return conversation_store[key].copy()


def save_history(user_email: str, session_id: str, messages: list) -> None:
    key = get_session_key(user_email, session_id)
    with store_lock:
        conversation_store[key] = messages


def rag_search_base(
    query: str,
    document_id: int | None = None,
    user_email: str | None = None,
) -> str:
    if not user_email:
        return "Error: User not authenticated."

    if is_overview_query(query):
        docs, _ = get_document_chunks(document_id=document_id, user_email=user_email)
        if docs:
            return summarize(docs, max_length=1200)

    docs, metas = search(query=query, document_id=document_id, user_email=user_email)
    logger.info("Raw retrieval: %s chunks for query '%s'", len(docs), query)
    if not docs:
        return "No relevant information found."

    reranked_docs, _ = rerank_chunks(
        query=query,
        chunks=docs,
        metadatas=metas,
        top_k=6,
        threshold=0.3,
    )
    if not reranked_docs:
        logger.info("Reranker returned no chunks; falling back to top retrieved chunks.")
        return "\n\n".join(docs[:6])

    return "\n\n".join(reranked_docs)


def rag_summarize_base(
    document_id: int | None = None,
    user_email: str | None = None,
) -> str:
    if not user_email:
        return "Error: User not authenticated."

    docs, _ = get_document_chunks(document_id=document_id, user_email=user_email)
    return summarize(docs)


def rag_extract_base(
    field: str,
    document_id: int | None = None,
    user_email: str | None = None,
) -> str:
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
        citations.append(
            {
                "document_id": meta.get("document_id"),
                "source": meta.get("filename", "unknown"),
                "page": meta.get("page", "?"),
                "snippet": doc[:150] + ("..." if len(doc) > 150 else ""),
            }
        )
    return citations


@tool
def rag_search(query: str, document_id: int | None = None) -> str:
    """
    Search the user's uploaded documents for information relevant to the query.

    Args:
        query: The search question or keywords.
        document_id: Optional document ID to search within.
    """
    raise NotImplementedError("Must be executed with user context")


@tool
def rag_summarize(document_id: int | None = None) -> str:
    """
    Generate a concise summary of the user's documents.

    Args:
        document_id: Optional document ID to summarize.
    """
    raise NotImplementedError("Must be executed with user context")


@tool
def rag_extract(field: str, document_id: int | None = None) -> str:
    """
    Extract structured information from documents, such as names, emails, or dates.

    Args:
        field: The type of information to extract.
        document_id: Optional document ID to extract from.
    """
    raise NotImplementedError("Must be executed with user context")


class ChatRequest(BaseModel):
    message: str
    document_id: int | None = None
    session_id: str | None = None


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
        cleaned["document_id"] = (
            int(doc_id) if doc_id is not None and str(doc_id).isdigit() else None
        )

    elif tool_name == "rag_summarize":
        doc_id = args.get("document_id")
        if isinstance(doc_id, dict):
            doc_id = None
        cleaned["document_id"] = (
            int(doc_id) if doc_id is not None and str(doc_id).isdigit() else None
        )

    elif tool_name == "rag_extract":
        field = args.get("field", "")
        if isinstance(field, dict):
            field = ""
        cleaned["field"] = str(field) if field else ""

        doc_id = args.get("document_id")
        if isinstance(doc_id, dict):
            doc_id = None
        cleaned["document_id"] = (
            int(doc_id) if doc_id is not None and str(doc_id).isdigit() else None
        )

    return cleaned


SYSTEM_PROMPT = """You are an intelligent document assistant with access to the user's uploaded documents.

CRITICAL RULES:
1. ONLY say "I don't have information about that in your uploaded documents" when:
   - the rag_search tool returns exactly "No relevant information found."
   - OR the tool returns empty / no chunks at all.

2. If the tool returns ANY content, even partial content, you MUST:
   - Use that content as the basis for your answer.
   - Never ignore it or say you don't have information.
   - Summarize, explain, or quote from it naturally.
   - Cite source file name and page when possible.

3. NEVER make up information or use external/general knowledge for questions that are clearly about the user's documents.

4. When information IS found, always include citations like [filename, page X] where available.

5. If retrieved content is not directly relevant, politely say so and ask for clarification. Do not default to "no information" unless truly nothing was found.

TOOL USAGE RULES:
- Use rag_search for factual retrieval.
- Use rag_summarize for summaries or overviews.
- Use rag_extract for names, emails, dates, and other structured data.
- Always provide 'query' as a STRING.
- 'document_id' should be INTEGER or null, never an object.
"""


@router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not request.message or not request.message.strip():
        return StreamingResponse(
            iter(["data: [DONE]\n\n"]),
            media_type="text/event-stream",
        )

    user_email = current_user["email"]
    session_id = request.session_id or str(uuid.uuid4())
    history = get_history(user_email, session_id)

    if not history:
        history = [SystemMessage(content=SYSTEM_PROMPT)]

    messages = history + [HumanMessage(content=request.message)]
    model_with_tools = llm.bind_tools([rag_search, rag_summarize, rag_extract])

    def execute_rag_search(args):
        return rag_search_base(**args, user_email=user_email)

    def execute_rag_summarize(args):
        return rag_summarize_base(**args, user_email=user_email)

    def execute_rag_extract(args):
        return rag_extract_base(**args, user_email=user_email)

    final_citations = []

    def stream_response():
        nonlocal final_citations, messages

        yield f"data: {json.dumps({'session_id': session_id})}\n\n"
        tool_call_results = {}
        used_documents = False

        try:
            if is_overview_query(request.message) or (
                request.document_id is not None
                and is_document_followup_query(request.message)
            ):
                docs, metas = get_document_chunks(
                    document_id=request.document_id,
                    user_email=user_email,
                )
                if docs:
                    used_documents = True
                    final_citations = build_citations(docs, metas)
                    context = summarize(docs, max_length=3000)
                    overview_response = llm.invoke(
                        [
                            SystemMessage(
                                content=(
                                    "Answer the user's question using only the provided document context. "
                                    "Do not mention tools, function calls, JSON, or implementation details. "
                                    "For follow-up requests, expand on the previous answer with concrete details from the context."
                                )
                            ),
                            HumanMessage(
                                content=(
                                    f"Question: {request.message}\n\n"
                                    f"Document context:\n{context}"
                                )
                            ),
                        ]
                    )
                    content = (
                        overview_response.content
                        if hasattr(overview_response, "content")
                        else str(overview_response)
                    )
                    messages.append(AIMessage(content=content))

                    for word in content.split():
                        yield f"data: {json.dumps({'content': word + ' '})}\n\n"

                    yield f"data: {json.dumps({'citations': final_citations})}\n\n"
                    return

            for chunk in model_with_tools.stream(messages):
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    tool_call = chunk.tool_calls[0]
                    tool_name = tool_call["name"]
                    args = tool_call["args"]
                    tool_id = tool_call["id"]

                    logger.info("Tool called: %s", tool_name)
                    logger.info("Raw args: %s", json.dumps(args, indent=2))

                    try:
                        cleaned_args = validate_and_clean_args(tool_name, args)
                        if (
                            request.document_id is not None
                            and cleaned_args.get("document_id") is None
                        ):
                            cleaned_args["document_id"] = request.document_id

                        logger.info("Cleaned args: %s", json.dumps(cleaned_args, indent=2))

                        if tool_name == "rag_search":
                            if not cleaned_args.get("query"):
                                result = "Error: Search query cannot be empty. Please provide a search term."
                            else:
                                result = execute_rag_search(cleaned_args)
                                docs, metas = search(**cleaned_args, user_email=user_email)
                                reranked_docs, reranked_metas = rerank_chunks(
                                    query=cleaned_args.get("query", ""),
                                    chunks=docs,
                                    metadatas=metas,
                                    top_k=6,
                                )
                                final_citations = build_citations(
                                    reranked_docs,
                                    reranked_metas,
                                )
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
                        logger.error("Tool error: %s", str(tool_error), exc_info=True)
                        result = f"Error executing tool: {str(tool_error)}"

                    if (
                        "No relevant information found" not in result
                        and result.strip()
                        and not result.startswith("Error:")
                    ):
                        used_documents = True

                    tool_call_results[tool_id] = result
                    logger.info("Tool result first 200 chars: %s", result[:200])

                    messages.append(chunk)
                    messages.append(ToolMessage(content=result, tool_call_id=tool_id))
                    break

            if tool_call_results:
                logger.info("Generating final answer")
                final_response = llm.invoke(messages)

                if hasattr(final_response, "content"):
                    content = final_response.content
                elif isinstance(final_response, str):
                    content = final_response
                else:
                    content = str(final_response)

                if not content.strip():
                    content = "I don't have that information in your documents."

                messages.append(AIMessage(content=content))

                for word in content.split():
                    yield f"data: {json.dumps({'content': word + ' '})}\n\n"

            if used_documents and final_citations:
                yield f"data: {json.dumps({'citations': final_citations})}\n\n"
            else:
                yield f"data: {json.dumps({'citations': []})}\n\n"

        except Exception as e:
            logger.error("Stream error: %s", str(e), exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            logger.info("Saving %s messages for session %s", len(messages), session_id)
            save_history(user_email, session_id, messages)
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")
