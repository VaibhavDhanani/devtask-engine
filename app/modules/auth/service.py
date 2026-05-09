from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.modules.auth.schema import TokenPair
from app.modules.auth.utils import create_token, decode_token
from app.modules.user.model import User
from app.modules.user.repository import UserRepository
from app.modules.user.utils import verify_password


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def authenticate(self, email: EmailStr, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            # Same error for both cases — don't leak which one failed.
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise ForbiddenError("Account is inactive")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_token(user.id, "access"),
            refresh_token=create_token(user.id, "refresh"),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        user_id = decode_token(refresh_token, expected_type="refresh")
        user = await self.users.get(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid refresh token")
        return self.issue_tokens(user)
