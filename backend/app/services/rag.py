import os
import json
from openai import OpenAI
from .supabase_client import get_supabase

EMBEDDING_MODEL = "text-embedding-3-small"

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_embedding(text: str) -> list:
    """Create a vector embedding for a piece of text."""
    client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def store_framework_document(title: str, category: str, content: str, metadata: dict = None):
    """Embed and store a framework document in Supabase."""
    supabase = get_supabase()
    embedding = create_embedding(content)
    
    result = supabase.table("framework_documents").insert({
        "title": title,
        "category": category,
        "content": content,
        "embedding": embedding,
        "metadata": json.dumps(metadata) if metadata else None,
    }).execute()
    
    return result.data[0] if result.data else None

def retrieve_relevant_frameworks(query: str, match_count: int = 5, threshold: float = 0.5) -> list:
    """Search for framework documents most relevant to the query."""
    supabase = get_supabase()
    query_embedding = create_embedding(query)
    
    result = supabase.rpc("match_framework_documents", {
        "query_embedding": query_embedding,
        "match_threshold": threshold,
        "match_count": match_count,
    }).execute()
    
    return result.data if result.data else []

def build_framework_context(responses: list, max_docs: int = 5) -> str:
    """Build a framework context string from user responses.
    
    Takes the user's diagnostic responses, creates a summary query,
    retrieves the most relevant framework documents, and returns
    them as a formatted string for the Sonnet prompt.
    """
    # Build a summary of what the user described
    summary_parts = []
    for r in responses:
        summary_parts.append(f"{r['response_value']}")
    
    query = " ".join(summary_parts)
    
    # Retrieve relevant frameworks
    docs = retrieve_relevant_frameworks(query, match_count=max_docs)
    
    if not docs:
        # Fallback: return a minimal framework description
        return get_fallback_framework()
    
    # Format retrieved documents
    context_parts = []
    for doc in docs:
        context_parts.append(f"### {doc['title']} ({doc['category']})\n{doc['content']}")
    
    return "\n\n".join(context_parts)

def get_fallback_framework() -> str:
    """Minimal fallback if no documents are retrieved."""
    return """
Gensyn identifies challenges across two dimensions:

Challenge Types (upstream to downstream):
Connection → Clarity → Coherence → Insight → Experimentation → Execution → Momentum

Challenge Dynamics:
Internal (team, culture, process) | External (market, customer, partners) | Transitional (change, growth, disruption)

The upstream principle: address the earliest broken link first.
"""
