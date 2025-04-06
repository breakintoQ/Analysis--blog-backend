from fastapi import FastAPI, Request
import httpx
import logging

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = "http://user_service:8001/users"
ARTICLE_SERVICE_URL = "http://article_service:8002/articles"

logger = logging.getLogger("uvicorn")

@app.post("/users/register/")
async def register(request: Request):
    body = await request.json()
    logger.info(f"Request body: {body}")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/register/", json=body)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        if response.status_code != 200:
            return {"error": f"Failed to register user: {response.status_code}", "details": response.text}
        try:
            return response.json()
        except httpx.JSONDecodeError:
            return {"error": "Invalid JSON response", "details": response.text}

@app.post("/users/login/")
async def login(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/login/", json=body)
    return response.json()
