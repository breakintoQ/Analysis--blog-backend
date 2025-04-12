from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from openai import OpenAI
import socket
import httpx
from database.database import init_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from config import OPENAI_API_KEY, OPENAI_BASE_URL
import spacy
import re

app = FastAPI(title="AI Service")

SERVICE_NAME = "ai_service"
SERVICE_ID = "ai_service-1"
SERVICE_PORT = 8004
CONSUL_HOST = "consul"
CONSUL_PORT = 8500

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 加载 spaCy 中文模型
nlp = spacy.load("zh_core_web_sm")

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
        # 文本预处理
        doc = nlp(text_data.text)
        tokens = [token.text for token in doc]
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

        # 构造提示词
        prompt = f"""
请对以下文本执行以下操作，并按照如下格式返回：

【总结】：xxx  
【情感】：xxx  
【关键词】：关键词1，关键词2，关键词3...

文本原文：
{text_data.text}

辅助信息：
- 分词（前30个）：{', '.join(tokens[:30])}
- 实体识别：{', '.join([f"{e['text']}({e['label']})" for e in entities])}
        """

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "user", "content": prompt.strip()}
            ],
        )

        content = response.choices[0].message.content

        # 正则解析结果
        summary = re.search(r"【总结】：(.+?)\n", content)
        sentiment = re.search(r"【情感】：(.+?)\n", content)
        keywords = re.search(r"【关键词】：(.+)", content)

        return {
            "summary": summary.group(1).strip() if summary else None,
            "sentiment": sentiment.group(1).strip() if sentiment else None,
            "keywords": [kw.strip() for kw in keywords.group(1).split("，")] if keywords else [],
        }

    except Exception as e:
        print(f"错误信息：{e}")
        print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
        return {"error": str(e)}

app.include_router(router)