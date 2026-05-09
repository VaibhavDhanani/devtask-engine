from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import get_current_user
from app.modules.content.schema import ContentCreate, ContentRead, ContentUpdate
from app.modules.content.service import ContentService
from app.modules.user.model import User
from app.shared.dependencies import get_db, get_db_transactional

router = APIRouter()


@router.post("", response_model=ContentRead, status_code=status.HTTP_201_CREATED)
async def create_content(
    data: ContentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_transactional),
) -> ContentRead:
    content = await ContentService(db).create(user.id, data)
    return ContentRead.model_validate(content)


@router.get("", response_model=list[ContentRead])
async def list_content(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentRead]:
    items = await ContentService(db).list_for_owner(user.id, limit=limit, offset=offset)
    return [ContentRead.model_validate(c) for c in items]


@router.get("/{content_id}", response_model=ContentRead)
async def get_content(
    content_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentRead:
    content = await ContentService(db).get_for_owner(content_id, user.id)
    return ContentRead.model_validate(content)


@router.patch("/{content_id}", response_model=ContentRead)
async def update_content(
    content_id: UUID,
    data: ContentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_transactional),
) -> ContentRead:
    content = await ContentService(db).update(content_id, user.id, data)
    return ContentRead.model_validate(content)


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_transactional),
) -> None:
    await ContentService(db).delete(content_id, user.id)
