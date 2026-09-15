from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSourceResponse,
)
from app.security.rate_limiter import (
    enforce_chat_rate_limit,
)
from app.security.resource_access import (
    get_conversation_for_project,
)
from app.services.conversation_service import (
    create_conversation,
    get_conversation_messages,
    save_assistant_message,
    save_user_message,
)
from app.services.project_embedding_service import (
    EmbeddingConfigurationError,
)
from app.services.rag_service import (
    RagHistoryMessage,
    answer_project_question,
)
from app.db.models import User
from app.security.current_user import (
    get_current_user,
)
from app.security.resource_access import (
    get_conversation_for_project,
    get_indexed_project_for_user,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
    _rate_limit: None = Depends(
        enforce_chat_rate_limit,
    ),
) -> ChatResponse:
    project = get_indexed_project_for_user(
        db=db,
        project_id=request.project_id,
        user_id=current_user.id,
    )

    try:
        history: list[
            RagHistoryMessage
        ] = []

        if request.conversation_id:
            conversation = (
                get_conversation_for_project(
                    db=db,
                    conversation_id=(
                        request.conversation_id
                    ),
                    project_id=project.id,
                )
            )

            previous_messages = (
                get_conversation_messages(
                    db=db,
                    conversation_id=(
                        conversation.id
                    ),
                )
            )

            history = [
                RagHistoryMessage(
                    role=message.role,
                    content=message.content,
                )
                for message
                in previous_messages
            ]

        else:
            conversation = (
                create_conversation(
                    db=db,
                    project_id=project.id,
                    first_message=(
                        request.message
                    ),
                )
            )

        save_user_message(
            db=db,
            conversation_id=conversation.id,
            content=request.message,
        )

        result = (
            answer_project_question(
                db=db,
                project_id=project.id,
                question=request.message,
                top_k=request.top_k,
                history=history,
            )
        )

        sources = [
            {
                "path": source.path,
                "language": source.language,
                "chunk_index": (
                    source.chunk_index
                ),
                "excerpt": source.excerpt,
            }
            for source in result.sources
        ]

        save_assistant_message(
            db=db,
            conversation_id=conversation.id,
            content=result.answer,
            sources=sources,
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except EmbeddingConfigurationError as exc:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "El servicio de IA no está "
                "disponible."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise

    return ChatResponse(
        conversation_id=conversation.id,
        answer=result.answer,
        sources=[
            ChatSourceResponse(
                path=source.path,
                language=source.language,
                chunk_index=(
                    source.chunk_index
                ),
                excerpt=source.excerpt,
            )
            for source in result.sources
        ],
    )