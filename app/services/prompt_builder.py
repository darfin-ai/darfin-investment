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

Write a warm, polished Korean report using this exact Markdown-like structure:

### 한눈에 보는 진단
2 short sentences. Wrap the single most important diagnosis in **bold**.

### 지금 가장 중요한 포인트
- **포인트 이름**: one practical interpretation based on the metrics.
- **포인트 이름**: one practical interpretation based on the metrics.
- **포인트 이름**: one practical interpretation based on the metrics.

### 다음 리밸런싱 때 볼 것
- **체크할 것**: concrete action for simulated-investment learning.
- **체크할 것**: concrete action for simulated-investment learning.
- **체크할 것**: concrete action for simulated-investment learning.

Style rules:
- Keep it friendly and modern, not stiff.
- Use **bold** only for important labels, numbers, or warnings.
- Avoid long paragraphs. Prefer readable short lines.
- Do not use tables.

Important:
- Do not claim certainty.
- Do not say this is personalized financial advice.
- Make it clear that this is for simulated-investment learning.
""".strip()
