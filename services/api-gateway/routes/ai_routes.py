from fastapi import APIRouter, Request
from httpx import AsyncClient, Timeout

router = APIRouter(prefix="/ai", tags=["AI"])

AI_SERVICE_URL = "http://ai_service:8004/ai"


@router.post("/summarize/")
async def summarize(request: Request):
    body = await request.json()
    async with AsyncClient(timeout=Timeout(60.0)) as client:
        response = await client.post(f"{AI_SERVICE_URL}/summarize/", json=body)
    return response.json()