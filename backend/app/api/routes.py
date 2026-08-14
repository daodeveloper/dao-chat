from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import uuid
import json
import logging

from ..database import SessionLocal
from ..models import ChatMessage, ChatSession, SessionFeedback, Lead
from ..config import Config
from ..rag import rag_instance

logger = logging.getLogger(__name__)
router = APIRouter()


def get_client_info(request: Request) -> dict:
    headers = dict(request.headers)
    return {
        "ip_address": request.client.host if request.client else "Unknown",
        "user_agent": headers.get("user-agent", "Unknown"),
        "accept_language": headers.get("accept-language", "Unknown"),
        "platform": headers.get("sec-ch-ua-platform", "Unknown").strip('"'),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/session")
async def create_session(request: Request):
    """Start a chat session. Works with or without a database."""
    session_id = str(uuid.uuid4())
    try:
        await rag_instance.create_session(session_id)
    except Exception as e:
        logger.error(f"Error creating RAG session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start session")

    if Config.USE_DB:
        try:
            async with SessionLocal() as db:
                db.add(ChatSession(
                    id=session_id,
                    user_id=request.client.host if request.client else None,
                    session_metadata=get_client_info(request),
                    created_at=datetime.utcnow(),
                    is_active=True,
                ))
                await db.commit()
        except Exception as e:
            logger.warning(f"Session DB logging skipped: {e}")

    return {"session_id": session_id, "message": "New session created successfully"}


@router.post("/ask")
async def ask_question(request: Request, text: dict):
    """Answer a question over SSE. Persists to DB only when USE_DB is on."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session ID provided")
    if not text or not text.get("text") or not text["text"].strip():
        raise HTTPException(status_code=400, detail="Invalid or empty question")

    question = text["text"]

    if session_id not in rag_instance.active_sessions:
        await rag_instance.create_session(session_id)

    if Config.USE_DB:
        try:
            async with SessionLocal() as db:
                db.add(ChatMessage(
                    session_id=session_id, role="user", content=question,
                    message_metadata={"timestamp": datetime.utcnow().isoformat()},
                ))
                await db.commit()
        except Exception as e:
            logger.warning(f"User-message DB logging skipped: {e}")

    async def generate():
        bot_response = ""
        try:
            async for token in await rag_instance.stream_query(question, session_id):
                if token and isinstance(token, str):
                    bot_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"

            if not bot_response:
                yield f"data: {json.dumps({'error': 'No response generated'})}\n\n"
                return

            if Config.USE_DB:
                try:
                    async with SessionLocal() as db:
                        msg = ChatMessage(
                            session_id=session_id, role="bot", content=bot_response,
                            message_metadata={"timestamp": datetime.utcnow().isoformat()},
                        )
                        db.add(msg)
                        await db.commit()
                        await db.refresh(msg)
                        yield f"data: {json.dumps({'message_id': msg.id})}\n\n"
                except Exception as e:
                    logger.warning(f"Bot-message DB logging skipped: {e}")
        except Exception as e:
            logger.error(f"Error in stream generation: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/wati")
async def wati_webhook(payload: dict, request: Request):
    """WhatsApp entry point for WATI. One reply per message, keyed by number."""
    if Config.WATI_SHARED_SECRET and request.headers.get("X-DAO-Secret") != Config.WATI_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    phone = str(payload.get("waId") or payload.get("phone") or payload.get("whatsappNumber") or "").strip()
    question = (payload.get("text") or payload.get("message") or payload.get("body") or "").strip()
    if not phone or not question:
        raise HTTPException(status_code=400, detail="Missing phone or text")

    session_id = f"wa-{phone}"
    if session_id not in rag_instance.active_sessions:
        await rag_instance.create_session(session_id)

    try:
        answer = await rag_instance.get_answer(question, session_id)
    except Exception as e:
        logger.error(f"WATI answer error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating reply")

    if Config.USE_DB:
        try:
            async with SessionLocal() as db:
                session = None
                from sqlalchemy import select
                res = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
                session = res.scalar_one_or_none()
                if not session:
                    db.add(ChatSession(
                        id=session_id, user_id=phone,
                        session_metadata={"channel": "whatsapp", "phone": phone},
                        created_at=datetime.utcnow(), is_active=True,
                    ))
                db.add(ChatMessage(session_id=session_id, role="user", content=question,
                                   message_metadata={"channel": "whatsapp"}))
                db.add(ChatMessage(session_id=session_id, role="bot", content=answer,
                                   message_metadata={"channel": "whatsapp"}))
                await db.commit()
        except Exception as e:
            logger.warning(f"WATI DB logging skipped: {e}")

    return {"reply": answer or "Let me connect you to our team."}


@router.post("/lead")
async def capture_lead(payload: dict, request: Request):
    """Save an interested person (only when a database is enabled)."""
    if Config.WATI_SHARED_SECRET and request.headers.get("X-DAO-Secret") != Config.WATI_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not Config.USE_DB:
        return {"status": "skipped", "reason": "database disabled"}
    try:
        async with SessionLocal() as db:
            lead = Lead(
                phone=str(payload.get("phone") or payload.get("waId") or "").strip() or None,
                name=payload.get("name"),
                source=payload.get("source") or "whatsapp",
                intent=payload.get("intent"),
                project_interest=payload.get("project_interest"),
                message=payload.get("message"),
                created_at=datetime.utcnow(),
            )
            db.add(lead)
            await db.commit()
            await db.refresh(lead)
            return {"status": "success", "lead_id": lead.id}
    except Exception as e:
        logger.error(f"Lead capture error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error saving lead")


# --- Feedback endpoints: no-op without a database so the UI never errors ---

@router.post("/message/{message_id}/feedback")
async def message_feedback(message_id: int, feedback: dict):
    if not Config.USE_DB:
        return {"status": "ok"}
    try:
        async with SessionLocal() as db:
            msg = await db.get(ChatMessage, message_id)
            if not msg:
                raise HTTPException(status_code=404, detail="Message not found")
            msg.thumbs_up = feedback.get("thumbs_up", False)
            msg.thumbs_down = feedback.get("thumbs_down", False)
            msg.feedback_timestamp = datetime.utcnow()
            await db.commit()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"message feedback skipped: {e}")
        return {"status": "ok"}


@router.post("/message/{message_id}/detailed-feedback")
async def message_detailed_feedback(message_id: int, feedback: dict):
    # Frontend calls this; accept and store text when DB is on, else no-op.
    if not Config.USE_DB:
        return {"status": "ok"}
    try:
        async with SessionLocal() as db:
            msg = await db.get(ChatMessage, message_id)
            if msg:
                meta = msg.message_metadata or {}
                meta["detailed_feedback"] = feedback.get("feedback_text") or feedback
                msg.message_metadata = meta
                await db.commit()
        return {"status": "success"}
    except Exception as e:
        logger.warning(f"detailed feedback skipped: {e}")
        return {"status": "ok"}


@router.post("/session/{session_id}/feedback")
async def session_feedback(session_id: str, feedback: dict):
    if not Config.USE_DB:
        return {"status": "ok"}
    try:
        async with SessionLocal() as db:
            db.add(SessionFeedback(
                session_id=session_id,
                rating=feedback.get("rating"),
                feedback_text=feedback.get("feedback_text"),
                email=feedback.get("email"),
                created_at=datetime.utcnow(),
            ))
            await db.commit()
        return {"status": "success"}
    except Exception as e:
        logger.warning(f"session feedback skipped: {e}")
        return {"status": "ok"}


@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    if session_id in rag_instance.active_sessions:
        await rag_instance._remove_session(session_id)
    if Config.USE_DB:
        try:
            async with SessionLocal() as db:
                from sqlalchemy import select
                res = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
                s = res.scalar_one_or_none()
                if s:
                    s.is_active = False
                    s.ended_at = datetime.utcnow()
                    await db.commit()
        except Exception as e:
            logger.warning(f"end session DB skipped: {e}")
    return {"message": "Session ended successfully"}
