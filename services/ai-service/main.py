from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from openai import OpenAI
import socket
import httpx
from database.database import init_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from config import OPENAI_API_KEY, OPENAI_BASE_URL

app = FastAPI(title="AI Service")

SERVICE_NAME = "ai_service"
SERVICE_ID = "ai_service-1"
SERVICE_PORT = 8004
CONSUL_HOST = "consul"
CONSUL_PORT = 8500

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

class TextData(BaseModel):
    text: str

router = APIRouter(prefix="/ai", tags=["AI"])

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

@router.post("/summarize/")
async def summarize(text_data: TextData):
    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "user", "content": f" 进行智能总结：\n\n{text_data.text}"}
            ],
        )
        # 提取生成的摘要内容
        summary = response.choices[0].message.content
        return {"summary": summary}
    except Exception as e:
        print(f"错误信息：{e}")
        print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")

app.include_router(router)