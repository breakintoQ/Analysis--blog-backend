from fastapi import FastAPI, Depends, HTTPException, APIRouter
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth import create_access_token
from database.database import get_db, init_db
from database.models import User 
import logging

logger = logging.getLogger("uvicorn")

app = FastAPI(title="User Service")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class UserLogin(BaseModel):
    username: str
    password: str

router = APIRouter(prefix="/users", tags=["Users"])

@app.on_event("startup")
async def startup_event():
    init_db()

@router.post("/register/")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    logger.info(f"Registering user: {user.username}")
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # 创建新用户
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password, email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"username": new_user.username, "user_id": str(new_user.id)}

@router.post("/login/")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    # 使用 ORM 查询用户
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalars().first()

    # 检查用户是否存在以及密码是否正确
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # 生成 JWT Token
    token = create_access_token(user_id=str(db_user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(db_user.id),
        "username": db_user.username,
    }

app.include_router(router)