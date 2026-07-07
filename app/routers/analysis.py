from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.calculator import analyze_portfolio_state, build_portfolio_report, calculate_metrics
from app.services.gemini_client import generate_analysis, generate_analysis_with_usage
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
    metrics: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)
    prompt: str
    analysis: str | None = None


@router.post("", response_model=AnalysisResponse)
async def analyze_company(payload: AnalysisRequest) -> AnalysisResponse:
    metrics = calculate_metrics(payload.financials)
    prompt = build_analysis_prompt(
        ticker=payload.ticker,
        company_name=payload.company_name,
        financials=payload.financials,
        metrics=metrics,
    )
    analysis, _ = await generate_analysis_with_usage(prompt)

    return AnalysisResponse(
        ticker=payload.ticker.upper(),
        metrics=metrics,
        prompt=prompt,
        analysis=analysis,
    )


@router.post("/portfolio", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(payload: PortfolioAnalysisRequest) -> PortfolioAnalysisResponse:
    if payload.state:
        metrics = analyze_portfolio_state(payload.state, payload.stocks)
        report = build_portfolio_report(metrics, payload.nickname)
    else:
        metrics = payload.metrics
        report = payload.report

    prompt = build_portfolio_prompt(metrics=metrics, report=report)
    analysis, _ = await generate_analysis_with_usage(prompt)
    # Fallback: if AI returns empty, generate a short summary so UI doesn't show an empty box
    if not analysis or (isinstance(analysis, str) and not analysis.strip()):
        nickname = payload.nickname or report.get("nickname") or "사용자"
        label = report.get("label") or "-"
        label_reason = report.get("labelReason") or ""
        advice_items = [str(item.get("t")) for item in (report.get("adviceTop3") or []) if item.get("t")]
        advice_text = ", ".join(advice_items) if advice_items else "특별한 권장사항이 없어요"
        analysis = f"{nickname}님의 내 주식 진단: {label}. {label_reason} 주요 권장사항: {advice_text}."

    return PortfolioAnalysisResponse(
        metrics=metrics,
        report=report,
        prompt=prompt,
        analysis=analysis,
    )
