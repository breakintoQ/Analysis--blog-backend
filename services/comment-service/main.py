from fastapi import FastAPI, HTTPException,APIRouter, Depends
from pydantic import BaseModel
from typing import List
import uuid
import socket
import httpx
import logging
from database.database import init_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Article as DBArticle
from database.models import Comment as DBComment
from database.models import User as DBUser
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload   


app = FastAPI(title="Comment Service")

SERVICE_NAME = "comment_service"
SERVICE_ID = "comment_service-1"
SERVICE_PORT = 8003
CONSUL_HOST = "consul"
CONSUL_PORT = 8500

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Comment(BaseModel):
    id: int = None
    article_id: int
    user_id: int
    content: str
    parent_id: int = None


router = APIRouter(prefix="/comments", tags=["Comments"])


@app.on_event("startup")
async def startup_event():
    await init_db()
    ip = socket.gethostbyname(socket.gethostname())
    url = f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/agent/service/register"
    data = {
        "ID": SERVICE_ID,
        "Name": SERVICE_NAME,
        "Address": ip,
        "Port": SERVICE_PORT,
        "Check": {
            "HTTP": f"http://{ip}:{SERVICE_PORT}/health",
            "Interval": "10s"
        }
    }
    async with httpx.AsyncClient() as client:
        try:
            res = await client.put(url, json=data)
            print(f"Consul register status: {res.status_code}")
        except Exception as e:
            print(f"Failed to register with Consul: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/article/{article_id}")
async def get_comments_by_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBComment)
        .where(DBComment.article_id == article_id)
    )
    comments = result.scalars().all()

    response = []

    for comment in comments:
        username_result = await db.execute(
            select(DBUser.username).where(DBUser.id == comment.user_id)
        )   
        username = username_result.scalars().first()
        response.append({
            "id": comment.id,
            "article_id": comment.article_id,
            "user_id": comment.user_id,
            "username": username,
            "content": comment.content,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at,
        })
    return response


@router.post("/")
async def add_comment(comment: Comment, db: AsyncSession = Depends(get_db)):
    # 检查文章是否存在
    article_result = await db.execute(select(DBArticle).where(DBArticle.id == comment.article_id))
    if not article_result.scalars().first():
        raise HTTPException(status_code=404, detail="Article not found")

    # 检查用户是否存在
    user_result = await db.execute(select(DBUser).where(DBUser.id == comment.user_id))
    if not user_result.scalars().first():
        raise HTTPException(status_code=404, detail="User not found")
    
    username_result = await db.execute(
        select(DBUser.username).where(DBUser.id == comment.user_id)
    )
    username = username_result.scalars().first()

    # 创建评论
    new_comment = DBComment(
        article_id=comment.article_id,
        user_id=comment.user_id,
        content=comment.content,
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return {
        "id": new_comment.id,
        "article_id": new_comment.article_id,
        "user_id": new_comment.user_id,
        "username": username,
        "content": new_comment.content,
        "created_at": new_comment.created_at,
    }

# @router.delete("/{comment_id}")
# async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBComment).where(DBComment.id == comment_id))
#     comment = result.scalars().first()
#     if not comment:
#         raise HTTPException(status_code=404, detail="Comment not found")

#     await db.delete(comment)
#     await db.commit()

#     return {"detail": "Comment deleted successfully"}


@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    # 查询要删除的评论
    result = await db.execute(select(DBComment).where(DBComment.id == comment_id))
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # 查询并删除所有子评论（递归删除）
    async def delete_replies(parent_id: int):
        replies_result = await db.execute(select(DBComment).where(DBComment.parent_id == parent_id))
        replies = replies_result.scalars().all()
        for reply in replies:
            await delete_replies(reply.id)  # 递归删除子评论
            await db.delete(reply)

    await delete_replies(comment_id)

    # 删除主评论
    await db.delete(comment)
    await db.commit()

    return {"detail": "Comment and its replies deleted successfully"}

@router.post("/reply/")
async def reply_to_comment(comment: Comment, db: AsyncSession = Depends(get_db)):
    # 检查父评论是否存在
    parent_result = await db.execute(select(DBComment).where(DBComment.id == comment.parent_id))
    parent_comment = parent_result.scalars().first()
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Parent comment not found")

    # 检查文章是否存在
    article_result = await db.execute(select(DBArticle).where(DBArticle.id == comment.article_id))
    if not article_result.scalars().first():
        raise HTTPException(status_code=404, detail="Article not found")

    # 检查用户是否存在
    user_result = await db.execute(select(DBUser).where(DBUser.id == comment.user_id))
    if not user_result.scalars().first():
        raise HTTPException(status_code=404, detail="User not found")
    
    username_result = await db.execute(
        select(DBUser.username).where(DBUser.id == comment.user_id)
    )
    username = username_result.scalars().first()

    # 创建回复
    new_comment = DBComment(
        article_id=comment.article_id,
        user_id=comment.user_id,
        content=comment.content,
        parent_id=comment.parent_id,
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return {
        "id": new_comment.id,
        "article_id": new_comment.article_id,
        "user_id": new_comment.user_id,
        "username": username,
        "content": new_comment.content,
        "parent_id": new_comment.parent_id,
        "created_at": new_comment.created_at,
    }

app.include_router(router)