from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.analysis import router as analysis_router

app = FastAPI(
    title="Darfin 투자 분석 서버",
    description="4대 축 계산 + Gemini AI 리포트 생성 (Python FastAPI)",
    version="1.0.0",
)

# CORS — React 개발 서버(localhost:5173)에서 호출 가능
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(analysis_router)


@app.get("/")
def health_check():
    return {"status": "ok", "server": "darfin-analysis"}
