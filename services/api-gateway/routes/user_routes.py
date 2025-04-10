from fastapi import APIRouter, Request
import httpx

router = APIRouter(prefix="/users", tags=["Users"])

USER_SERVICE_URL = "http://user_service:8001/users"

@router.post("/register/")
async def register(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/register/", json=body)
        if response.status_code != 200:
            return {"error": f"Failed to register user: {response.status_code}", "details": response.text}
        try:
            return response.json()
        except httpx.JSONDecodeError:
            return {"error": "Invalid JSON response", "details": response.text}

@router.post("/login/")
async def login(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/login/", json=body)
    return response.json()