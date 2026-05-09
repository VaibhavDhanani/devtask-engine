from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.user.model import User
from app.modules.user.repository import UserRepository
from app.modules.user.schema import UserCreate, UserUpdate
from app.modules.user.utils import hash_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def create(self, data: UserCreate) -> User:
        if await self.repo.get_by_email(data.email):
            raise ConflictError("A user with that email already exists")
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        return await self.repo.add(user)

    async def get(self, user_id: UUID) -> User:
        user = await self.repo.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[User]:
        return await self.repo.list(limit=limit, offset=offset)

    async def update(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.session.flush()
        return user

    async def delete(self, user_id: UUID) -> None:
        user = await self.get(user_id)
        await self.repo.delete(user)
