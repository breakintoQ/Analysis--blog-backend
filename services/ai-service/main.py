from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_BASE_URL

app = FastAPI(title="AI Service")


chat_model = ChatOpenAI(
    model_name="qwen-plus",
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_BASE_URL
)

class TextData(BaseModel):
    text: str

@app.post("/summarize/")
async def summarize(text_data: TextData):
    # 使用 LangChain 的 ChatOpenAI 接口生成摘要
    response = chat_model.generate(
        [{"role": "user", "content": f"Summarize this: {text_data.text}"}]
    )
    # 提取生成的内容
    summary = response.generations[0][0].text.strip()
    return {"summary": summary}
