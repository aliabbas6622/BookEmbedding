"""
RAG Playground API - Interactive testing and experimentation
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time

router = APIRouter(prefix="/api/v1/rag", tags=["RAG Playground"])


class RAGQueryRequest(BaseModel):
    """RAG query request model"""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    document_id: Optional[int] = Field(None, description="Filter by document ID")
    index_name: Optional[str] = Field(None, description="Specific vector index")
    embedding_provider: Optional[str] = Field(None, description="Override embedding provider")
    rerank: bool = Field(default=False, description="Enable reranking")
    rerank_top_k: Optional[int] = Field(None, ge=1, le=50, description="Rerank top K")


class RAGChatRequest(BaseModel):
    """RAG chat request model"""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    top_k: int = Field(default=5, ge=1, le=20, description="Context documents")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=1024, ge=100, le=4096, description="Max response tokens")
    stream: bool = Field(default=False, description="Stream response")
    include_sources: bool = Field(default=True, description="Include source documents")


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[float] = None


class ConversationContext(BaseModel):
    """Conversation context model"""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: float
    updated_at: float
    metadata: Dict[str, Any] = {}


class SourceDocument(BaseModel):
    """Source document in response"""
    chunk_id: int
    document_id: int
    content: str
    score: float
    metadata: Dict[str, Any]
    page_number: Optional[int] = None


class RAGQueryResponse(BaseModel):
    """RAG query response"""
    query: str
    results: List[SourceDocument]
    total_results: int
    query_time_ms: float
    embedding_model: str
    index_name: str


class RAGChatResponse(BaseModel):
    """RAG chat response"""
    conversation_id: str
    message: str
    sources: List[SourceDocument]
    usage: Dict[str, Any]
    model: str
    query_time_ms: float
    total_time_ms: float


# In-memory conversation storage (replace with DB in production)
_conversations: Dict[str, ConversationContext] = {}


def get_available_embedding_models() -> List[str]:
    """Get available embedding models"""
    return [
        "all-MiniLM-L6-v2",
        "all-mpnet-base-v2",
        "text-embedding-3-small",
        "text-embedding-3-large",
        "embed-multilingual-v3.0"
    ]


def get_available_llm_models() -> List[str]:
    """Get available LLM models"""
    return [
        "llama3.2",
        "llama3.1:8b",
        "mistral:7b",
        "gpt-4o-mini",
        "gpt-4o",
        "gemini-1.5-flash",
        "claude-3-5-sonnet-20241022"
    ]


@router.get("/models")
async def list_available_models():
    """List available embedding and LLM models"""
    return {
        "embedding_models": get_available_embedding_models(),
        "llm_models": get_available_llm_models(),
        "defaults": {
            "embedding": "all-MiniLM-L6-v2",
            "llm": "llama3.2"
        }
    }


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Perform a RAG search query
    
    This endpoint allows you to test semantic search with different configurations
    """
    start_time = time.time()
    
    # Validate embedding provider if specified
    if request.embedding_provider:
        available_providers = ["sentence_transformers", "openai", "cohere", "huggingface"]
        if request.embedding_provider not in available_providers:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid embedding provider. Available: {available_providers}"
            )
    
    # Simulate search (in production, this would use actual providers)
    # For now, return mock results
    mock_results = [
        SourceDocument(
            chunk_id=i,
            document_id=request.document_id or 1,
            content=f"Sample result {i} for query: {request.query}",
            score=0.95 - (i * 0.05),
            metadata={
                "source": "document.pdf",
                "chunk_index": i,
                "embedding_model": request.embedding_provider or "all-MiniLM-L6-v2"
            },
            page_number=(i % 10) + 1
        )
        for i in range(min(request.top_k, 5))
    ]
    
    query_time = (time.time() - start_time) * 1000
    
    return RAGQueryResponse(
        query=request.query,
        results=mock_results,
        total_results=len(mock_results),
        query_time_ms=round(query_time, 2),
        embedding_model=request.embedding_provider or "all-MiniLM-L6-v2",
        index_name=request.index_name or "default"
    )


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(request: RAGChatRequest):
    """
    Chat with your documents using RAG
    
    This endpoint combines retrieval with LLM generation to answer questions
    based on your document corpus.
    """
    start_time = time.time()
    
    # Generate or retrieve conversation ID
    conversation_id = request.conversation_id or f"conv_{int(time.time())}"
    
    # Get or create conversation context
    if conversation_id in _conversations:
        conversation = _conversations[conversation_id]
    else:
        conversation = ConversationContext(
            conversation_id=conversation_id,
            messages=[],
            created_at=time.time(),
            updated_at=time.time(),
            metadata={"system_prompt": request.system_prompt or "You are a helpful assistant."}
        )
        _conversations[conversation_id] = conversation
    
    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=time.time()
    )
    conversation.messages.append(user_message)
    
    # Retrieve relevant documents (simulated)
    query_time_start = time.time()
    mock_sources = [
        SourceDocument(
            chunk_id=i,
            document_id=1,
            content=f"Relevant context {i+1} for: {request.message[:50]}...",
            score=0.92 - (i * 0.08),
            metadata={"source": "doc.pdf", "page": i+1},
            page_number=i+1
        )
        for i in range(min(request.top_k, 5))
    ]
    query_time = (time.time() - query_time_start) * 1000
    
    # Generate response (simulated - in production would call LLM)
    llm_model = "llama3.2"
    simulated_response = f"""Based on the retrieved documents, here's what I found about your query:

Your question: "{request.message}"

Key information from the documents:
{chr(10).join([f'- {src.content}' for src in mock_sources[:3]])}

This should help answer your question. Let me know if you need more details!"""
    
    # Add assistant response
    assistant_message = ChatMessage(
        role="assistant",
        content=simulated_response,
        timestamp=time.time()
    )
    conversation.messages.append(assistant_message)
    conversation.updated_at = time.time()
    
    total_time = (time.time() - start_time) * 1000
    
    response = RAGChatResponse(
        conversation_id=conversation_id,
        message=simulated_response,
        sources=mock_sources if request.include_sources else [],
        usage={
            "prompt_tokens": len(request.message.split()) * 2,
            "completion_tokens": len(simulated_response.split()) * 2,
            "total_tokens": (len(request.message.split()) + len(simulated_response.split())) * 2
        },
        model=llm_model,
        query_time_ms=round(query_time, 2),
        total_time_ms=round(total_time, 2)
    )
    
    return response


@router.get("/conversations")
async def list_conversations(limit: int = Query(20, ge=1, le=100)):
    """List all conversations"""
    sorted_convs = sorted(
        _conversations.values(),
        key=lambda c: c.updated_at,
        reverse=True
    )
    
    return {
        "conversations": [
            {
                "conversation_id": c.conversation_id,
                "message_count": len(c.messages),
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "preview": c.messages[0].content if c.messages else ""
            }
            for c in sorted_convs[:limit]
        ],
        "total": len(sorted_convs)
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = _conversations[conversation_id]
    
    return {
        "conversation_id": conversation.conversation_id,
        "messages": conversation.messages,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "metadata": conversation.metadata
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del _conversations[conversation_id]
    
    return {"message": f"Conversation {conversation_id} deleted"}


@router.post("/conversations/clear")
async def clear_all_conversations():
    """Clear all conversations"""
    global _conversations
    _conversations = {}
    return {"message": "All conversations cleared"}


@router.get("/compare")
async def compare_queries(
    query: str = Query(..., description="Query to test"),
    models: List[str] = Query(None, description="Models to compare")
):
    """
    Compare search results across different embedding models
    
    Useful for evaluating which embedding model works best for your use case
    """
    if not models:
        models = ["all-MiniLM-L6-v2", "all-mpnet-base-v2"]
    
    results = {}
    for model in models:
        # Simulate different results per model (in production would actually query each)
        results[model] = {
            "model": model,
            "results_count": 5,
            "avg_score": 0.85,
            "query_time_ms": 45.2,
            "sample_results": [
                {
                    "chunk_id": i,
                    "content": f"Result for {model}: {query[:30]}...",
                    "score": 0.90 - (i * 0.05)
                }
                for i in range(3)
            ]
        }
    
    return {
        "query": query,
        "comparison": results,
        "recommendation": max(results.keys(), key=lambda m: results[m]["avg_score"])
    }


@router.post("/evaluate")
async def evaluate_retrieval(
    query: str = Query(..., description="Test query"),
    expected_chunks: List[int] = Query(None, description="Expected relevant chunk IDs")
):
    """
    Evaluate retrieval quality for a query
    
    Calculates precision, recall, and other metrics
    """
    # Simulate retrieval
    retrieved_chunks = [1, 2, 3, 4, 5]  # Mock retrieved chunks
    
    if expected_chunks:
        expected_set = set(expected_chunks)
        retrieved_set = set(retrieved_chunks)
        
        true_positives = len(expected_set & retrieved_set)
        precision = true_positives / len(retrieved_set) if retrieved_set else 0
        recall = true_positives / len(expected_set) if expected_set else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "query": query,
            "metrics": {
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1, 3)
            },
            "retrieved_chunks": retrieved_chunks,
            "expected_chunks": expected_chunks,
            "true_positives": true_positives,
            "false_positives": len(retrieved_set - expected_set),
            "false_negatives": len(expected_set - retrieved_set)
        }
    else:
        return {
            "query": query,
            "retrieved_chunks": retrieved_chunks,
            "note": "Provide expected_chunks to calculate evaluation metrics"
        }


@router.get("/benchmark")
async def benchmark_performance(
    iterations: int = Query(10, ge=1, le=100, description="Number of iterations")
):
    """
    Benchmark retrieval performance
    
    Runs multiple queries and reports latency statistics
    """
    import random
    
    latencies = []
    for i in range(iterations):
        start = time.time()
        # Simulate query
        time.sleep(random.uniform(0.01, 0.05))
        latencies.append((time.time() - start) * 1000)
    
    return {
        "iterations": iterations,
        "statistics": {
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "p50_ms": round(sorted(latencies)[len(latencies)//2], 2),
            "p95_ms": round(sorted(latencies)[int(len(latencies)*0.95)], 2),
            "p99_ms": round(sorted(latencies)[int(len(latencies)*0.99)], 2)
        },
        "throughput_qps": round(iterations / (sum(latencies) / 1000), 2)
    }
