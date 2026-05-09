from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.schema import LoginRequest, RefreshRequest, TokenPair
from app.modules.auth.service import AuthService
from app.modules.user.schema import UserCreate, UserRead
from app.modules.user.service import UserService
from app.shared.dependencies import get_db, get_db_transactional

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db_transactional),
) -> UserRead:
    user = await UserService(db).create(data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    service = AuthService(db)
    user = await service.authenticate(data.email, data.password)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    return await AuthService(db).refresh(data.refresh_token)
