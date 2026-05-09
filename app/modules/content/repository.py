from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.content.model import Content


class ContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, content_id: UUID) -> Content | None:
        return await self.session.get(Content, content_id)

    async def list_for_owner(
        self, owner_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Content]:
        stmt = (
            select(Content)
            .where(Content.owner_id == owner_id)
            .order_by(Content.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def add(self, content: Content) -> Content:
        self.session.add(content)
        await self.session.flush()
        return content

    async def delete(self, content: Content) -> None:
        await self.session.delete(content)
