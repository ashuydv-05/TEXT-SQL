from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from src.services.query_service import query_service
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="AI Data Analyst",
    description="Safe Text-to-SQL API for IPL analytics",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class VerificationResponse(BaseModel):
    status: str
    checks: list[str]
    errors: list[str] = []


class QueryResponse(BaseModel):
    question: str
    sql: Optional[str]
    verification: VerificationResponse
    result: list[dict]
    explanation: str
    latency_ms: float


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/v1/schema")
def get_schema():
    return {
        "message": "Schema endpoint will be connected next"
    }


@app.post("/v1/query", response_model=QueryResponse)
def query(request: QueryRequest):
    return query_service.process(request.question)
