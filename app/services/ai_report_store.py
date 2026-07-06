import json
from datetime import datetime
from uuid import uuid4
from typing import Any

from sqlalchemy.orm import Session

from app.core.db import Base, engine
from app.models.ai_report import AiReport
from app.models.user_trading_stats import UserTradingStats


_table_ready = False


def ensure_ai_reports_table() -> None:
    global _table_ready
    if _table_ready:
        return

    Base.metadata.create_all(bind=engine, tables=[AiReport.__table__])
    _table_ready = True


def save_ai_report(
    db: Session,
    *,
    metrics: dict[str, Any],
    report: dict[str, Any],
    prompt: str,
    analysis: str | None,
    user_id: str | None = None,
) -> AiReport:
    ensure_ai_reports_table()
    numeric_user_id = _parse_user_id(user_id)
    if numeric_user_id is None:
        raise ValueError("user_id is required to save ai_reports")

    health = report.get("health") if isinstance(report.get("health"), dict) else {}
    content = {
        "metrics": metrics,
        "report": report,
        "prompt": prompt,
        "analysis": analysis,
    }
    row = AiReport(
        user_id=numeric_user_id,
        health_score=str(health.get("total")) if health.get("total") is not None else None,
        tendency_label=report.get("label"),
        report_content=json.dumps(content, ensure_ascii=False),
        share_token=uuid4().hex,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def upsert_user_trading_stats(
    db: Session,
    *,
    user_id: str | None,
    metrics: dict[str, Any],
) -> UserTradingStats:
    numeric_user_id = _parse_user_id(user_id)
    if numeric_user_id is None:
        raise ValueError("user_id is required to save user_trading_stats")

    behavior = metrics.get("behavior") if isinstance(metrics.get("behavior"), dict) else {}
    values = {
        "monthly_trade_freq": _to_float(behavior.get("tradesPerMonth")),
        "avg_hold_days": _to_float(behavior.get("avgHoldDays")),
        "stop_loss_rate": _to_float(behavior.get("stopLossRatio")),
        "take_profit_rate": _to_float(behavior.get("takeProfitRatio")),
        "chase_buy_count": _to_int(behavior.get("chaseBuyCount")),
        "updated_at": datetime.utcnow(),
    }

    row = db.query(UserTradingStats).filter(UserTradingStats.user_id == numeric_user_id).one_or_none()
    if row is None:
        row = UserTradingStats(user_id=numeric_user_id, **values)
        db.add(row)
    else:
        for key, value in values.items():
            setattr(row, key, value)

    db.flush()
    return row


def list_ai_reports(db: Session, *, user_id: str | None, limit: int = 20) -> list[dict[str, Any]]:
    numeric_user_id = _parse_user_id(user_id)
    if numeric_user_id is None:
        return []

    rows = (
        db.query(AiReport)
        .filter(AiReport.user_id == numeric_user_id)
        .order_by(AiReport.created_at.desc(), AiReport.report_id.desc())
        .limit(limit)
        .all()
    )

    reports = []
    for row in rows:
        content = _parse_report_content(row.report_content)
        report = content.get("report") if isinstance(content.get("report"), dict) else {}
        report = _sanitize_loaded_report(report)
        report.update(
            {
                "remoteReportId": row.report_id,
                "geminiAnalysis": _sanitize_loaded_report(content.get("analysis")),
                "dbError": None,
                "ts": int(row.created_at.timestamp() * 1000) if row.created_at else None,
            }
        )
        reports.append(report)

    return reports


def _parse_user_id(user_id: str | None) -> int | None:
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_report_content(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _sanitize_loaded_report(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("undefined", "미분류")
    if isinstance(value, list):
        return [_sanitize_loaded_report(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_loaded_report(item) for key, item in value.items()}
    return value
