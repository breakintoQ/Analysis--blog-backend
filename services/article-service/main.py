from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

app = FastAPI(title="Article Service")

class Article(BaseModel):
    id: str = None
    title: str
    content: str
    tags: List[str]

db = {}

@app.post("/articles/")
def create_article(article: Article):
    article.id = str(uuid.uuid4())
    db[article.id] = article
    return article

@app.get("/articles/{article_id}")
def get_article(article_id: str):
    if article_id not in db:
        raise HTTPException(status_code=404, detail="Article not found")
    return db[article_id]
