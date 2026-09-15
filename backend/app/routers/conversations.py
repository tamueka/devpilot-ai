from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)
from app.security.current_user import (
    get_current_user,
)
from app.security.resource_access import (
    get_conversation_for_user,
    get_project_for_user,
)
from app.services.conversation_service import (
    get_conversation_messages,
    get_project_conversations,
)


router = APIRouter(
    tags=["Conversations"],
)


@router.get(
    "/projects/{project_id}/conversations",
    response_model=list[ConversationResponse],
)
def list_project_conversations(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
) -> list[ConversationResponse]:
    project = get_project_for_user(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )

    conversations = get_project_conversations(
        db=db,
        project_id=project.id,
    )

    return [
        ConversationResponse.model_validate(
            conversation,
        )
        for conversation in conversations
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation_detail(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
) -> ConversationDetailResponse:
    conversation = get_conversation_for_user(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    messages = get_conversation_messages(
        db=db,
        conversation_id=conversation.id,
    )

    return ConversationDetailResponse(
        id=conversation.id,
        project_id=conversation.project_id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[
            MessageResponse.model_validate(
                message,
            )
            for message in messages
        ],
    )