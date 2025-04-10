from fastapi import APIRouter, Request
import httpx

router = APIRouter(prefix="/articles", tags=["Articles"])

ARTICLE_SERVICE_URL = "http://article_service:8002/articles"

@router.post("/")
async def create_article(request: Request):
    body = await request.json()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(f"{ARTICLE_SERVICE_URL}/", json=body)
    return response.json()

@router.get("/{article_id}/")
async def get_article(article_id: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:  # 启用自动跟随重定向
        response = await client.get(f"{ARTICLE_SERVICE_URL}/{article_id}/")
        if response.status_code == 404:
            return {"detail": "Article not found"}
        elif response.status_code != 200:
            return {"detail": f"Error from article-service: {response.status_code}"}
        return response.json()

@router.get("/")
async def get_articles():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(f"{ARTICLE_SERVICE_URL}/")
    return response.json()

@router.delete("/{article_id}/")
async def delete_article(article_id: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.delete(f"{ARTICLE_SERVICE_URL}/{article_id}/")
    return response.json()

@router.put("/{article_id}/")
async def update_article(article_id: str, request: Request):
    body = await request.json()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.put(f"{ARTICLE_SERVICE_URL}/{article_id}/", json=body)
    return response.json()

@router.get("/tag/{tag_name}/")
async def get_articles_by_tag(tag_name: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(f"{ARTICLE_SERVICE_URL}/tag/{tag_name}/")
    return response.json()