from typing import Any


def _format_mapping(values: dict[str, Any]) -> str:
    if not values:
        return "- No data provided"

    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def build_analysis_prompt(
    ticker: str,
    company_name: str | None,
    financials: dict[str, Any],
    metrics: dict[str, float | None],
) -> str:
    name = company_name or ticker.upper()

    return f"""
You are an equity research assistant for Darfin Investment.
Analyze the company below in a concise, practical style.

Company: {name}
Ticker: {ticker.upper()}

Financial data:
{_format_mapping(financials)}

Calculated metrics:
{_format_mapping(metrics)}

Please provide:
1. Business and financial summary
2. Strengths
3. Risks
4. Investment view
""".strip()


def build_portfolio_prompt(metrics: dict[str, Any], report: dict[str, Any]) -> str:
    nickname = report.get("nickname") or "사용자"

    return f"""
You are Darfin's portfolio coaching assistant.
The user is using a simulated trading service. Do not recommend a specific buy or sell order.
Use the calculated metrics as facts, and provide practical learning-oriented feedback in Korean.
Address the user as "{nickname}님" in the Korean report.

Calculated metrics:
{_format_mapping(metrics)}

Existing rule-based report:
{_format_mapping(report)}

Write a concise Korean report with this structure:
1. 핵심 진단: 2~3문장
2. 행동 패턴 해석
3. 리스크 해석
4. 수익률 해석
5. 다음 행동 제안 3가지

Important:
- Do not claim certainty.
- Do not say this is personalized financial advice.
- Make it clear that this is for simulated-investment learning.
""".strip()
