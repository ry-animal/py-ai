"""Enhanced chat interface with document citations and intelligent routing."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .agent_service import AgentService
from .dependencies import get_agent_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """A chat message with optional citations."""

    content: str
    sources: list[dict] | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Response from the chat system."""

    message: str
    sources: list[dict] | None = None
    routing_info: dict
    session_id: str


class ChatRequest(BaseModel):
    """Request to the chat system."""

    message: str = Field(min_length=1, description="The user's question or message")
    session_id: str | None = None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    """Send a message and get an AI response with citations."""
    # Generate response using agent
    final_state = {}
    session_key = request.session_id or "default"

    # Get history and create state
    history = await agent_service.memory.read(session_key)
    from langchain_core.messages import HumanMessage

    state = {
        "question": request.message,
        "messages": history + [HumanMessage(content=request.message)],
        "log": [],
    }

    # Run the agent graph
    config = {"configurable": {"thread_id": session_key}}
    async for event in agent_service.graph.astream(state, config=config):
        for node_state in event.values():
            if isinstance(node_state, dict):
                final_state.update(node_state)

    # Generate final answer
    contexts = final_state.get("contexts", [])
    sources = final_state.get("sources", [])
    direct_answer = final_state.get("direct_answer")

    if contexts:
        if sources:
            # Format contexts with source information for the LLM
            context_with_sources = []
            for i, source in enumerate(sources):
                context_with_sources.append(
                    f"[Source {i + 1}: {source.get('source', 'Unknown')}]\n{source.get('content', '')}"
                )
            formatted_contexts = "\n\n".join(context_with_sources)
        else:
            formatted_contexts = "\n\n".join(contexts)

        answer = await agent_service.ai.generate_answer(request.message, [formatted_contexts])

        # Add citation instruction
        if sources:
            citation_prompt = "\n\nWhen referencing information, please cite your sources using [Source X] notation."
            answer = await agent_service.ai.generate_answer(
                request.message + citation_prompt, [formatted_contexts]
            )
    else:
        answer = "I don't have enough information to answer your question."
        if direct_answer:
            answer = direct_answer

    # Save to memory
    await agent_service._commit_turn(session_key, request.message, answer)

    # Prepare routing info
    routing_info = {
        "route": final_state.get("route", "unknown"),
        "route_reason": final_state.get("route_reason", ""),
        "log": final_state.get("log", []),
    }

    return ChatResponse(
        message=answer, sources=sources, routing_info=routing_info, session_id=session_key
    )


@router.get("/stream")
async def chat_stream(
    q: str = Query(..., description="The user's question"),
    session: str | None = Query(None, description="Session ID for conversation continuity"),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Stream a chat response with real-time updates."""

    async def generate():
        session_key = session or "default"

        try:
            async for chunk in agent_service.answer(q, stream=True, session=session):
                # Format as server-sent events
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service),
):
    """Get chat history for a session."""
    messages = await agent_service.memory.read(session_id)

    formatted_history = []
    for i in range(0, len(messages), 2):
        if i + 1 < len(messages):
            human_msg = messages[i]
            ai_msg = messages[i + 1]
            formatted_history.append(
                {
                    "user": human_msg.content,
                    "assistant": ai_msg.content,
                    "timestamp": getattr(human_msg, "timestamp", None),
                }
            )

    return {
        "session_id": session_id,
        "messages": formatted_history,
        "total": len(formatted_history),
    }


@router.delete("/sessions/{session_id}")
async def clear_chat_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service),
):
    """Clear a chat session."""
    # Clear memory for this session
    await agent_service.memory.clear(session_id)

    return {"message": f"Session {session_id} cleared successfully"}
