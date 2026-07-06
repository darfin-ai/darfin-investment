from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.calculator import analyze_portfolio_state, build_portfolio_report, calculate_metrics
from app.services.ai_report_store import list_ai_reports, save_ai_report, upsert_user_trading_stats
from app.services.gemini_client import generate_analysis
from app.services.prompt_builder import build_analysis_prompt, build_portfolio_prompt


router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., examples=["AAPL"])
    company_name: str | None = Field(default=None, examples=["Apple Inc."])
    financials: dict[str, Any] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    ticker: str
    metrics: dict[str, float | None]
    prompt: str
    analysis: str | None = None


class PortfolioAnalysisRequest(BaseModel):
    user_id: str | None = None
    nickname: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    stocks: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)


class PortfolioAnalysisResponse(BaseModel):
    report_id: int | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)
    prompt: str
    analysis: str | None = None
    db_error: str | None = None


class PortfolioReportsResponse(BaseModel):
    reports: list[dict[str, Any]]


@router.post("", response_model=AnalysisResponse)
async def analyze_company(payload: AnalysisRequest) -> AnalysisResponse:
    metrics = calculate_metrics(payload.financials)
    prompt = build_analysis_prompt(
        ticker=payload.ticker,
        company_name=payload.company_name,
        financials=payload.financials,
        metrics=metrics,
    )
    analysis = await generate_analysis(prompt)

    return AnalysisResponse(
        ticker=payload.ticker.upper(),
        metrics=metrics,
        prompt=prompt,
        analysis=analysis,
    )


@router.post("/portfolio", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(
    payload: PortfolioAnalysisRequest,
    db: Session = Depends(get_db),
) -> PortfolioAnalysisResponse:
    if payload.state:
        metrics = analyze_portfolio_state(payload.state, payload.stocks)
        report = build_portfolio_report(metrics, payload.nickname)
    else:
        metrics = payload.metrics
        report = payload.report

    prompt = build_portfolio_prompt(metrics=metrics, report=report)
    analysis = await generate_analysis(prompt)
    report_id = None
    db_error = None

    try:
        upsert_user_trading_stats(
            db,
            user_id=payload.user_id,
            metrics=metrics,
        )
        saved = save_ai_report(
            db,
            user_id=payload.user_id,
            metrics=metrics,
            report=report,
            prompt=prompt,
            analysis=analysis,
        )
        report_id = saved.report_id
    except Exception as exc:
        db.rollback()
        db_error = f"{type(exc).__name__}: {exc}"

    return PortfolioAnalysisResponse(
        report_id=report_id,
        metrics=metrics,
        report=report,
        prompt=prompt,
        analysis=analysis,
        db_error=db_error,
    )


@router.get("/portfolio/reports/{user_id}", response_model=PortfolioReportsResponse)
def get_portfolio_reports(
    user_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> PortfolioReportsResponse:
    reports = list_ai_reports(db, user_id=user_id, limit=max(1, min(limit, 50)))
    return PortfolioReportsResponse(reports=reports)
