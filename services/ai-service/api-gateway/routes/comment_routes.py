from fastapi import APIRouter, Request
import httpx

router = APIRouter(prefix="/comments", tags=["Comments"])

COMMENT_SERVICE_URL = "http://comment_service:8003/comments"

@router.post("/")
async def add_comment(request: Request):
    body = await request.json()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(f"{COMMENT_SERVICE_URL}/", json=body)
    return response.json()  

@router.get("/article/{article_id}/")
async def get_comments_by_article(article_id: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(f"{COMMENT_SERVICE_URL}/article/{article_id}/")
        return response.json()
    
@router.delete("/{comment_id}/")
async def delete_comment(comment_id: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.delete(f"{COMMENT_SERVICE_URL}/{comment_id}/")
        return response.json()

@router.post("/reply/")
async def add_reply(request: Request):
    body = await request.json()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(f"{COMMENT_SERVICE_URL}/reply/", json=body)
    return response.json()