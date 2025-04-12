from fastapi import FastAPI, Request
import httpx
import socket
import logging
from routes.user_routes import router as user_router
from routes.article_routes import router as article_router
from routes.comment_routes import router as comment_router


app = FastAPI(title="API Gateway")

SERVICE_NAME = "api-gateway"
SERVICE_ID = "api-gateway-1"
SERVICE_PORT = 8000
CONSUL_HOST = "consul"
CONSUL_PORT = 8500

logger = logging.getLogger("api-gateway")
logger.setLevel(logging.INFO)   


@app.on_event("startup")
async def startup_event():
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
            logger.info(f"Consul register status: {res.status_code}")
        except Exception as e:
            logger.error(f"Failed to register with Consul: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(user_router)
app.include_router(article_router)
app.include_router(comment_router)