from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.content.model import Content
from app.modules.content.repository import ContentRepository
from app.modules.content.schema import ContentCreate, ContentUpdate


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContentRepository(session)

    async def create(self, owner_id: UUID, data: ContentCreate) -> Content:
        content = Content(title=data.title, body=data.body, owner_id=owner_id)
        return await self.repo.add(content)

    async def get_for_owner(self, content_id: UUID, owner_id: UUID) -> Content:
        content = await self.repo.get(content_id)
        if content is None:
            raise NotFoundError("Content not found")
        if content.owner_id != owner_id:
            # Hide existence from non-owners — return 404, not 403.
            raise NotFoundError("Content not found")
        return content

    async def list_for_owner(
        self, owner_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Content]:
        return await self.repo.list_for_owner(owner_id, limit=limit, offset=offset)

    async def update(
        self, content_id: UUID, owner_id: UUID, data: ContentUpdate
    ) -> Content:
        content = await self.get_for_owner(content_id, owner_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(content, field, value)
        await self.session.flush()
        return content

    async def delete(self, content_id: UUID, owner_id: UUID) -> None:
        content = await self.get_for_owner(content_id, owner_id)
        await self.repo.delete(content)
