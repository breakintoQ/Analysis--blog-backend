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
from database.models import Tag as DBTag
from database.models import User as DBUser
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload   


app = FastAPI(title="Article Service")

SERVICE_NAME = "article_service"
SERVICE_ID = "article_service-1"
SERVICE_PORT = 8002
CONSUL_HOST = "consul"
CONSUL_PORT = 8500

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Article(BaseModel):
    id: str = None
    title: str
    content: str
    author_id: str
    tags: List[str] = []

class UpdateArticle(BaseModel):
    title: str
    content: str
    tags: List[str] = []

router = APIRouter(prefix="/articles", tags=["Articles"])


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


"""新建文章"""
@router.post("/")
async def create_article(article: Article, db: AsyncSession = Depends(get_db)):
    # 创建文章 ID
    new_article = DBArticle(
        title=article.title,
        content=article.content,
        author_id=article.author_id
    )
    db.add(new_article)

    author = await db.execute(select(DBUser.username).where(DBUser.id == article.author_id))
    author_name = author.scalars().first()

    # 显式加载 tags 关联数据
    await db.refresh(new_article, attribute_names=["tags"])

    # 处理标签
    for tag_name in article.tags:
        result = await db.execute(select(DBTag).where(DBTag.name == tag_name))
        tag = result.scalars().first()
        if not tag:
            tag = DBTag(name=tag_name)
            db.add(tag)
        new_article.tags.append(tag)

    await db.commit()
    await db.refresh(new_article)
    return {"author_id":new_article.author_id, "author_name": author_name, "title": new_article.title, "tags": [tag.name for tag in new_article.tags]}

"""获取所有文章"""
@router.get("/")
async def get_articles(db: AsyncSession = Depends(get_db)):
    # 查询所有文章
    result = await db.execute(select(DBArticle))
    articles = result.scalars().all()

    # 构造返回结果
    response = []
    for article in articles:
        # 查询作者名称
        author_result = await db.execute(select(DBUser.username).where(DBUser.id == article.author_id))
        author_name = author_result.scalars().first()

        # 查询文章的标签
        tag_result = await db.execute(
            select(DBTag)
            .join(DBTag.articles)
            .where(DBArticle.id == article.id)
        )
        tags = [tag.name for tag in tag_result.scalars().all()]

        # 构造文章的响应数据
        response.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "author_name": author_name,
            "author_id": article.author_id,
            "tags": tags
        })

    return response

@router.get("/{article_id}")
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBArticle).where(DBArticle.id == article_id))
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")    

    response= []

    author =await db.execute(select(DBUser.username).where(DBUser.id == article.author_id))
    author_name = author.scalars().first()

    tag_result = await db.execute(
            select(DBTag)
            .join(DBTag.articles)
            .where(DBArticle.id == article.id)
        )
    tags = [tag.name for tag in tag_result.scalars().all()]

    response.append({
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "author_name": author_name,
        "author_id": article.author_id,
        "tags": tags
    })
    return response


    
    
@router.put("/{article_id}")
async def update_article(article_id: str, article: UpdateArticle, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBArticle).where(DBArticle.id == article_id))
    db_article = result.scalars().first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")

    # 更新文章内容
    db_article.title = article.title
    db_article.content = article.content

    # 显式加载 tags 关联数据
    await db.refresh(db_article, attribute_names=["tags"])

    # 更新标签
    db_article.tags.clear()
    for tag_name in article.tags:
        result = await db.execute(select(DBTag).where(DBTag.name == tag_name))
        tag = result.scalars().first()
        if not tag:
            tag = DBTag(name=tag_name)
            db.add(tag)
        db_article.tags.append(tag)

    await db.commit()
    await db.refresh(db_article)
    return {"id": db_article.id , "title": db_article.title, "tags": [tag.name for tag in db_article.tags]}

@router.delete("/{article_id}")
async def delete_article(article_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBArticle).where(DBArticle.id == article_id))
    db_article = result.scalars().first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(db_article)
    await db.commit()
    return {"message": "Article deleted successfully"}

@router.get("/tag/{tag_name}")
async def get_articles_by_tag(tag_name: str, db: AsyncSession = Depends(get_db)):
    # 查询指定标签的文章
    result = await db.execute(
        select(DBArticle)
        .join(DBArticle.tags)
        .where(DBTag.name == tag_name)
    )
    articles = result.scalars().all()

    logger.info(f"Articles with tag '{tag_name}': {[article.title for article in articles]}")

    # 构造返回结果
    response = []
    for article in articles:
        # 查询作者名称
        author_result = await db.execute(select(DBUser.username).where(DBUser.id == article.author_id))
        author_name = author_result.scalars().first()

        # 构造文章的响应数据
        response.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "author_name": author_name,
            "author_id": article.author_id,
            "tags": [tag.name for tag in article.tags]
        })

    return response


app.include_router(router)