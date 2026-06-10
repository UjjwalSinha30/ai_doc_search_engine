# import os
# import sys
# import json
# from dotenv import load_dotenv

# load_dotenv(r"D:\projects\ai_knowledge_search_engine\ai_knowledge_search_engine\.env")

# from groq import Groq
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# # Test API works first
# response = client.chat.completions.create(
#     model="llama-3.3-70b-versatile",
#     messages=[{"role": "user", "content": "Say hello"}]
# )
# print("✅ Groq working:", response.choices[0].message.content)




import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(r"D:\projects\ai_knowledge_search_engine\ai_knowledge_search_engine\.env")

from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─── Import your RAG ──────────────────────────────────────────────────────────
sys.path.append(r"D:\projects\ai_knowledge_search_engine\ai_knowledge_search_engine\backend")

from api.helpers import search, rerank_chunks, get_document_chunks, summarize
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

USER_EMAIL = "l@gmail.com"  
DOCUMENT_ID = 36                       

ollama_llm = ChatOllama(
    model="qwen2.5:3b",
    base_url="http://localhost:11434",
    temperature=0.1
)

def get_rag_answer(question):
    docs, metas = search(query=question, document_id=DOCUMENT_ID, user_email=USER_EMAIL)
    if not docs:
        return "No information found.", ""
    
    reranked_docs, _ = rerank_chunks(
        query=question, chunks=docs, metadatas=metas, top_k=6, threshold=0.0
    )
    
    context = "\n\n".join(reranked_docs) if reranked_docs else "\n\n".join(docs[:3])
    
    response = ollama_llm.invoke([
        SystemMessage(content="Answer based only on the context provided. Be concise."),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}")
    ])
    return response.content, context

# ─── Evaluate with Groq ───────────────────────────────────────────────────────
def evaluate_with_groq(question, answer, context, ground_truth):
    prompt = f"""You are an evaluation judge. Score this RAG system response.

Question: {question}
Ground Truth: {ground_truth}
Retrieved Context: {context[:500]}
Generated Answer: {answer}

Score each metric from 0.0 to 1.0:
1. Faithfulness: Is the answer factually consistent with the context?
2. Answer Relevancy: Does the answer address the question?
3. Context Precision: Is the retrieved context relevant to the question?
4. Context Recall: Does the context contain enough info to answer correctly?

Respond ONLY in this JSON format with no explanation:
{{
  "faithfulness": 0.0,
  "answer_relevancy": 0.0,
  "context_precision": 0.0,
  "context_recall": 0.0
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

# ─── Test data ────────────────────────────────────────────────────────────────
questions = [
    "What is the purpose of a group in the HOW2HEAL app?",
    "What is HOW2HEAL community?",
    "How are clients automatically assigned to a group?",
    "What are the 3 ways a client can get into a group?",
    "What is the current state of the community wall?",
    "What is the purpose of a sequence?",
    "What does the coach need when putting a client in a sequence?",
    "Can cards currently be sent to groups?",
    "What is the desired card sending functionality?",
    "What are global HOW cards?",
    "What happens when a coach creates a card in their own profile?",
    "What is the issue with passio outputs?",
    "What is the login issue described in the document?",
    "What should happen if a card is on daily repeat?",
    "What is the desired improvement for the sequence assignment list?",
]

ground_truths = [
    "Grouping clients for communication, cards and sequence delivery.",
    "HOW2HEAL community is the main group clients are automatically assigned to upon registering.",
    "Clients are auto assigned into the main group HOW2HEAL community upon registering.",
    "Auto assigned upon registration, use of invite code, and push by coach to group.",
    "Not activated on the client side and missing the connection to sequences.",
    "Auto sending of scheduled cards and clients can choose a sequence to join within community.",
    "Assign a start date which can be today or a future cohort start date.",
    "No, cards can only be sent in the client profile right now.",
    "Cards should be able to send to groups, individual or all with cohort start date or send now options.",
    "Cards made under admin that are globally approved and every coach has access to send.",
    "Only that coach can send and edit it, not added to global library but visible in client profile once sent.",
    "Clients are tracking but coach cannot see the outputs. Clients are seeing other peoples inputs.",
    "Clients in pending need complete reset to use same email. Some resetting passwords still cannot get in.",
    "Bump back to the top versus send again for daily, bump back up on that day for weekly.",
    "Show more than 3 names per page.",
]

# ─── Run evaluation ───────────────────────────────────────────────────────────
print("🚀 Starting evaluation...\n")

all_scores = {
    "faithfulness": [],
    "answer_relevancy": [],
    "context_precision": [],
    "context_recall": []
}

for i, (question, ground_truth) in enumerate(zip(questions, ground_truths)):
    print(f"[{i+1}/3] {question[:55]}...")
    
    answer, context = get_rag_answer(question)
    scores = evaluate_with_groq(question, answer, context, ground_truth)
    
    for metric in all_scores:
        all_scores[metric].append(scores[metric])
    
    print(f"  ✅ F:{scores['faithfulness']:.2f} AR:{scores['answer_relevancy']:.2f} CP:{scores['context_precision']:.2f} CR:{scores['context_recall']:.2f}")

# ─── Final scores ─────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("📈 EVALUATION RESULTS (3 question test)")
print("="*50)

final = {k: sum(v)/len(v) for k, v in all_scores.items()}

print(f"Faithfulness:      {final['faithfulness']:.4f}")
print(f"Answer Relevancy:  {final['answer_relevancy']:.4f}")
print(f"Context Precision: {final['context_precision']:.4f}")
print(f"Context Recall:    {final['context_recall']:.4f}")
print("="*50)