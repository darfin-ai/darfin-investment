from time import time
from typing import Any


DAY_MS = 86_400_000
MONTH_MS = DAY_MS * 30
DISCLAIMER = "이 리포트는 모의투자 학습을 목적으로 제공되며, 특정 종목의 매수·매도를 권유하지 않아요."


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_divide(numerator: Any, denominator: Any) -> float | None:
    num = _to_float(numerator)
    den = _to_float(denominator)
    if num is None or den in (None, 0):
        return None
    return num / den


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _num(value: Any, default: float = 0) -> float:
    converted = _to_float(value)
    return converted if converted is not None else default


def _now_ms() -> int:
    return int(time() * 1000)


def _stock_for(code: str, stocks: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = fallback or {}
    stock = stocks.get(code) if isinstance(stocks.get(code), dict) else {}
    name = stock.get("name") or stock.get("stockName") or fallback.get("name") or fallback.get("short") or code
    price = _num(
        stock.get("price")
        if stock.get("price") is not None
        else fallback.get("currentPrice")
        if fallback.get("currentPrice") is not None
        else fallback.get("price")
        if fallback.get("price") is not None
        else fallback.get("avgPrice"),
    )

    return {
        **fallback,
        **stock,
        "code": code,
        "name": name,
        "stockName": name,
        "short": stock.get("short") or fallback.get("short") or name,
        "sector": stock.get("sector") or fallback.get("sector") or "미분류",
        "price": price,
    }


def _pct(value: float) -> str:
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.1f}%"


def _sign_num(value: Any) -> str:
    number = round(_num(value))
    return f"+{number:,}" if number > 0 else f"{number:,}"


def _charge_total(fund_history: list[Any]) -> float:
    latest_reset_ts = None
    for item in fund_history:
        if not isinstance(item, dict) or item.get("type") != "RESET":
            continue
        ts = _to_float(item.get("ts"))
        if ts is not None and (latest_reset_ts is None or ts > latest_reset_ts):
            latest_reset_ts = ts

    total = 0.0
    for item in fund_history:
        if not isinstance(item, dict) or item.get("type") != "CHARGE":
            continue
        ts = _to_float(item.get("ts"))
        if latest_reset_ts is not None and ts is not None and ts < latest_reset_ts:
            continue
        total += _num(item.get("amount"))
    return total


def calculate_metrics(financials: dict[str, Any]) -> dict[str, float | None]:
    revenue = financials.get("revenue")
    net_income = financials.get("net_income")
    total_assets = financials.get("total_assets")
    total_equity = financials.get("total_equity")
    total_debt = financials.get("total_debt")
    current_assets = financials.get("current_assets")
    current_liabilities = financials.get("current_liabilities")

    return {
        "net_margin": _safe_divide(net_income, revenue),
        "return_on_assets": _safe_divide(net_income, total_assets),
        "return_on_equity": _safe_divide(net_income, total_equity),
        "debt_to_equity": _safe_divide(total_debt, total_equity),
        "current_ratio": _safe_divide(current_assets, current_liabilities),
    }


def analyze_portfolio_state(state: dict[str, Any], stocks: dict[str, Any] | None = None) -> dict[str, Any]:
    stocks = stocks or {}
    funds = state.get("funds") if isinstance(state.get("funds"), dict) else {}
    raw_holdings = state.get("holdings") if isinstance(state.get("holdings"), list) else []
    trades = state.get("trades") if isinstance(state.get("trades"), list) else []
    watchlist = state.get("watchlist") if isinstance(state.get("watchlist"), list) else []
    fund_history = state.get("fundHistory") if isinstance(state.get("fundHistory"), list) else []
    now = _now_ms()

    seed = _num(funds.get("initialAmount"))
    cash = _num(funds.get("cashBalance"))
    charge_total = _charge_total(fund_history)
    contributed_capital = seed + charge_total
    holdings = []
    for item in raw_holdings:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "")
        if not code:
            continue
        stock = _stock_for(code, stocks, item)
        qty = _num(item.get("qty"))
        avg_price = _num(item.get("avgPrice"))
        evaluation = stock["price"] * qty
        cost = avg_price * qty
        pnl = evaluation - cost
        holdings.append(
            {
                **item,
                "code": code,
                "qty": qty,
                "avgPrice": avg_price,
                "stock": stock,
                "sector": stock["sector"],
                "eval": evaluation,
                "cost": cost,
                "pnl": pnl,
                "pnlPct": (pnl / cost * 100) if cost else 0,
            }
        )

    total_eval = sum(_num(item.get("eval")) for item in holdings)
    sells = [trade for trade in trades if isinstance(trade, dict) and trade.get("type") == "SELL"]
    buys = [trade for trade in trades if isinstance(trade, dict) and trade.get("type") == "BUY"]
    realized = sum(_num(trade.get("pnl")) for trade in sells)

    trade_timestamps = [_num(trade.get("ts")) for trade in trades if isinstance(trade, dict) and trade.get("ts")]
    first_ts = min(trade_timestamps) if trade_timestamps else now
    months = max(1, (now - first_ts) / MONTH_MS)

    trades_per_month = len(trades) / months
    first_buy_by_code: dict[str, float] = {}
    for trade in buys:
        code = str(trade.get("code") or "")
        ts = _num(trade.get("ts"))
        if code and (code not in first_buy_by_code or ts < first_buy_by_code[code]):
            first_buy_by_code[code] = ts

    durations = []
    for trade in sells:
        hold_days = _to_float(trade.get("holdDays"))
        if hold_days is not None:
            durations.append(hold_days)
            continue
        code = str(trade.get("code") or "")
        first_buy = first_buy_by_code.get(code)
        if first_buy:
            durations.append((_num(trade.get("ts")) - first_buy) / DAY_MS)
    for holding in holdings:
        first_buy = first_buy_by_code.get(str(holding.get("code") or ""))
        if first_buy:
            durations.append((now - first_buy) / DAY_MS)

    avg_hold_days = sum(durations) / len(durations) if durations else 0
    stop_loss_ratio = len([trade for trade in sells if _num(trade.get("pnl")) < 0]) / len(sells) * 100 if sells else 0
    take_profit_ratio = len([trade for trade in sells if _num(trade.get("pnl")) > 0]) / len(sells) * 100 if sells else 0
    chase_buy_count = 0
    for trade in buys:
        code = str(trade.get("code") or "")
        holding = next((item for item in raw_holdings if isinstance(item, dict) and item.get("code") == code), {})
        stock = _stock_for(code, stocks, holding or trade)
        if stock["price"] > 0 and _num(trade.get("price")) >= round(stock["price"] * 1.34) * 0.95:
            chase_buy_count += 1

    sector_eval: dict[str, float] = {}
    for holding in holdings:
        sector = str(holding.get("sector") or "미분류")
        sector_eval[sector] = sector_eval.get(sector, 0) + _num(holding.get("eval"))
    sector_count = len(sector_eval)
    top_sector_name = "-"
    top_sector_value = 0.0
    if sector_eval:
        top_sector_name, top_sector_value = max(sector_eval.items(), key=lambda item: item[1])
    sector_concentration = top_sector_value / total_eval * 100 if total_eval else 0

    top_stock = max(holdings, key=lambda item: _num(item.get("eval")), default=None)
    top_stock_eval = _num(top_stock.get("eval")) if top_stock else 0
    top_stock_concentration = top_stock_eval / total_eval * 100 if total_eval else 0
    loss_count = len([holding for holding in holdings if _num(holding.get("pnl")) < 0])
    loss_stock_ratio = loss_count / len(holdings) * 100 if holdings else 0
    risk_score = round(
        0.4 * min(100, sector_concentration)
        + 0.4 * min(100, top_stock_concentration)
        + 0.2 * min(100, loss_stock_ratio)
    )
    risk_grade = "낮음" if risk_score <= 40 else "보통" if risk_score <= 60 else "높음" if risk_score <= 80 else "매우 높음"

    total_assets = total_eval + cash
    investment_pnl = total_assets - contributed_capital
    total_return_pct = investment_pnl / contributed_capital * 100 if contributed_capital else 0
    contributions: dict[str, float] = {}
    for holding in holdings:
        code = str(holding.get("code") or "")
        contributions[code] = contributions.get(code, 0) + _num(holding.get("pnl"))
    for trade in sells:
        code = str(trade.get("code") or "")
        contributions[code] = contributions.get(code, 0) + _num(trade.get("pnl"))

    contrib_arr = []
    for code, value in contributions.items():
        holding = next((item for item in raw_holdings if isinstance(item, dict) and item.get("code") == code), {})
        stock = _stock_for(code, stocks, holding)
        contrib_arr.append({"code": code, "name": stock["name"], "sector": stock["sector"], "v": round(value)})
    top3 = sorted([item for item in contrib_arr if item["v"] > 0], key=lambda item: item["v"], reverse=True)[:3]
    bottom3 = sorted([item for item in contrib_arr if item["v"] < 0], key=lambda item: item["v"])[:3]

    sector_contrib_map: dict[str, float] = {}
    for item in contrib_arr:
        sector_contrib_map[item["sector"]] = sector_contrib_map.get(item["sector"], 0) + _num(item["v"])
    sector_contrib = sorted(
        [{"sector": sector, "v": round(value)} for sector, value in sector_contrib_map.items()],
        key=lambda item: item["v"],
        reverse=True,
    )

    dispersed = top_stock_concentration < 30 and sector_concentration <= 40 and sector_count >= 2
    if stop_loss_ratio < 10 and loss_count >= 2:
        label = "손실 회피형"
    elif len(watchlist) >= 8 and len(holdings) <= 1:
        label = "기회 손실형"
    elif avg_hold_days < 30:
        if top_stock_concentration > 30 and risk_grade in ("높음", "매우 높음"):
            label = "단기 집중 공격형"
        elif dispersed and risk_grade == "보통":
            label = "단기 분산형"
        else:
            label = "단기 집중 공격형" if top_stock_concentration > 30 else "단기 분산형"
    elif avg_hold_days <= 90:
        label = "중기 집중형" if top_stock_concentration > 30 else "중기 분산형"
    else:
        if top_stock_concentration > 30:
            label = "장기 집중형"
        elif dispersed and risk_grade == "낮음":
            label = "장기 분산 안정형"
        else:
            label = "장기 집중형"

    s_div = (12.5 if top_stock_concentration < 20 else 7 if top_stock_concentration < 30 else 3) + (
        12.5 if sector_count >= 3 else 7 if sector_count >= 2 else 3
    )
    s_risk = 25 if risk_grade == "낮음" else 16 if risk_grade == "보통" else 8 if risk_grade == "높음" else 2
    s_ret = 25 if total_return_pct > 10 else 18 if total_return_pct > 0 else 10 if total_return_pct > -10 else 3
    s_hab = (12.5 if 10 <= stop_loss_ratio <= 30 else 8 if not sells else 5) + (12.5 if chase_buy_count == 0 else 6)
    health_breakdown = {"분산도": round(s_div), "리스크관리": s_risk, "수익률": s_ret, "매매습관": round(s_hab)}
    health_total = sum(health_breakdown.values())
    health_grade = "우수" if health_total >= 70 else "보통" if health_total >= 50 else "개선 필요"

    return {
        "seed": seed,
        "chargeTotal": charge_total,
        "contributedCapital": contributed_capital,
        "totalAssets": total_assets,
        "investmentPnl": investment_pnl,
        "totalEval": total_eval,
        "cash": cash,
        "realized": realized,
        "totalReturnPct": total_return_pct,
        "months": months,
        "holdingsCount": len(holdings),
        "tradeCount": len(trades),
        "sellCount": len(sells),
        "watchCount": len(watchlist),
        "behavior": {
            "tradesPerMonth": trades_per_month,
            "avgHoldDays": avg_hold_days,
            "stopLossRatio": stop_loss_ratio,
            "takeProfitRatio": take_profit_ratio,
            "chaseBuyCount": chase_buy_count,
        },
        "risk": {
            "sectorConcentration": sector_concentration,
            "topSectorName": top_sector_name,
            "topStockConcentration": top_stock_concentration,
            "topStockName": top_stock["stock"]["name"] if top_stock else "-",
            "lossStockRatio": loss_stock_ratio,
            "lossCount": loss_count,
            "riskScore": risk_score,
            "riskGrade": risk_grade,
            "sectorCount": sector_count,
        },
        "returns": {"totalReturnPct": total_return_pct, "top3": top3, "bottom3": bottom3, "sectorContrib": sector_contrib},
        "label": label,
        "healthBreakdown": health_breakdown,
        "healthTotal": health_total,
        "healthGrade": health_grade,
        "dataLimited": len(trades) == 0,
        "behaviorLimited": len(sells) == 0,
    }


def build_portfolio_report(metrics: dict[str, Any], nickname: str | None = None) -> dict[str, Any]:
    behavior = metrics.get("behavior") or {}
    risk = metrics.get("risk") or {}
    returns = metrics.get("returns") or {}
    trades_per_month = _num(behavior.get("tradesPerMonth"))
    avg_hold_days = _num(behavior.get("avgHoldDays"))
    stop_loss_ratio = _num(behavior.get("stopLossRatio"))
    take_profit_ratio = _num(behavior.get("takeProfitRatio"))
    chase_buy_count = _to_int(behavior.get("chaseBuyCount"))
    top_stock_concentration = _num(risk.get("topStockConcentration"))
    sector_concentration = _num(risk.get("sectorConcentration"))
    risk_grade = risk.get("riskGrade") or "-"
    top_stock_name = risk.get("topStockName") or "-"
    top_sector_name = risk.get("topSectorName") or "-"
    total_return_pct = _num(metrics.get("totalReturnPct"))
    behavior_limited = bool(metrics.get("behaviorLimited"))

    freq_word = "빈번한(충동) 매매" if trades_per_month >= 6 else "중단기 매매" if trades_per_month >= 2 else "장기 보유 중심"
    hold_word = "단기" if avg_hold_days < 30 else "중기" if avg_hold_days <= 90 else "장기"
    label = metrics.get("label") or "-"
    label_reason = (
        f"평균 보유 {avg_hold_days:.0f}일({hold_word}형), 최대 종목 비중 {top_stock_concentration:.0f}%, "
        f"리스크 등급 '{risk_grade}'을 종합해 '{label}'으로 분류했어요."
    )

    health_grade = metrics.get("healthGrade") or "-"
    if health_grade == "우수":
        health_comment = "분산·리스크·수익·매매습관이 균형 잡혀 있어요. 현 전략을 유지하며 미세 조정만 권장해요."
    elif health_grade == "보통":
        health_comment = "전반적으로 무난하나 한두 축에서 개선 여지가 있어요. 아래 진단을 확인해보세요."
    else:
        health_comment = "여러 축에서 개선이 필요해요. 분산과 리스크 관리부터 점검하는 것을 권장해요."

    if behavior_limited:
        behavior_text = "매도 이력이 없어 손절·익절 습관은 분석이 제한돼요. 현재까지는 매수 후 보유 위주의 패턴이에요."
    else:
        behavior_text = (
            f"월 평균 {trades_per_month:.1f}회 거래로 {freq_word} 성향이에요. 평균 보유 기간은 {avg_hold_days:.0f}일({hold_word})이고, "
            f"손절 비율 {stop_loss_ratio:.0f}% · 익절 비율 {take_profit_ratio:.0f}%예요."
        )
        if stop_loss_ratio <= 10:
            behavior_text += " 손절을 거의 하지 않아 손실을 방치하는 경향이 보여요."
        elif stop_loss_ratio >= 30:
            behavior_text += " 손절이 잦아 매매 비용이 누적될 수 있어요."
        else:
            behavior_text += " 손절·익절 균형은 양호해요."
        if chase_buy_count >= 2:
            behavior_text += f" 52주 고가 부근 추격 매수가 {chase_buy_count}건 감지돼 진입 단가 관리가 필요해요."

    if chase_buy_count >= 2:
        behavior_advice = "고가 추격 매수를 줄이고 분할 매수로 평균 단가를 낮춰보세요."
    elif stop_loss_ratio <= 10:
        behavior_advice = "미리 손절 라인을 정해 손실 종목을 점검하는 습관을 들여보세요."
    else:
        behavior_advice = "현재 매매 습관은 안정적이에요. 규칙을 일관되게 유지하세요."

    risk_text = (
        f"리스크 점수 {_to_int(risk.get('riskScore'))}점으로 '{risk_grade}' 등급이에요. "
        f"업종 집중도는 {top_sector_name} {sector_concentration:.0f}%"
        + ("(매우 위험)" if sector_concentration > 60 else "(위험)" if sector_concentration > 40 else "(양호)")
        + f", 단일 종목 최대 비중은 {top_stock_name} {top_stock_concentration:.0f}%"
        + ("(매우 위험)" if top_stock_concentration > 50 else "(집중 위험)" if top_stock_concentration > 30 else "(양호)")
        + "예요."
    )
    if _num(risk.get("lossStockRatio")) > 50:
        risk_text += f" 보유 종목의 {_num(risk.get('lossStockRatio')):.0f}%가 평가손실 상태라 포트 점검이 필요해요."

    if sector_concentration > 40:
        risk_advice = f"{top_sector_name} 외 업종으로 분산해 섹터 쏠림을 완화하세요."
    elif top_stock_concentration > 30:
        risk_advice = f"{top_stock_name} 비중을 30% 이하로 조절해 종목 리스크를 낮추세요."
    else:
        risk_advice = "현재 분산 수준은 적정해요. 비중을 유지하세요."

    top3 = returns.get("top3") if isinstance(returns.get("top3"), list) else []
    bottom3 = returns.get("bottom3") if isinstance(returns.get("bottom3"), list) else []
    sector_contrib = returns.get("sectorContrib") if isinstance(returns.get("sectorContrib"), list) else []
    top_names = ", ".join(str(item.get("name") or item.get("code") or "-") for item in top3) if top3 else "없음"
    bottom_names = ", ".join(str(item.get("name") or item.get("code") or "-") for item in bottom3) if bottom3 else "없음"
    charge_total = _num(metrics.get("chargeTotal"))
    return_label = "충전액을 제외한 투자 수익률" if charge_total > 0 else "시드머니 대비 총 수익률"
    return_text = f"{return_label}은 {_pct(total_return_pct)}예요. 수익을 이끈 종목은 {top_names}이고, 손실 요인은 {bottom_names}이에요."
    if charge_total > 0:
        return_text += f" 자금 충전 {round(charge_total):,}원은 수익이 아니라 추가 원금으로 제외해 계산했어요."
    if sector_contrib:
        lead = sector_contrib[0]
        return_text += f" 업종별로는 {lead.get('sector')} 업종이 손익을 {'주도' if _num(lead.get('v')) >= 0 else '훼손'}했어요."

    advice_top3 = []
    if top_stock_concentration > 30:
        advice_top3.append({"t": "종목 집중도 완화", "d": f"{top_stock_name} 비중이 {top_stock_concentration:.0f}%로 높아요. 비중을 30% 이하로 줄여 단일 종목 리스크를 낮추세요."})
    if sector_concentration > 40:
        advice_top3.append({"t": "업종 분산", "d": f"{top_sector_name}에 {sector_concentration:.0f}%가 몰려 있어요. 다른 업종을 편입해 변동성을 분산하세요."})
    if chase_buy_count >= 2:
        advice_top3.append({"t": "추격 매수 자제", "d": f"고가 부근 추격 매수가 {chase_buy_count}건이에요. 분할 매수로 진입 단가를 관리하세요."})
    if stop_loss_ratio <= 10 and not behavior_limited:
        advice_top3.append({"t": "손절 규칙 수립", "d": "손절 비율이 낮아 손실이 누적될 수 있어요. 명확한 손절 기준을 세워보세요."})
    if _num(metrics.get("cash")) / (_num(metrics.get("totalEval")) + _num(metrics.get("cash")) or 1) < 0.15:
        advice_top3.append({"t": "현금 비중 확보", "d": "현금 비중이 15% 미만이에요. 추가 매수 여력을 위해 현금을 일부 확보하세요."})
    while len(advice_top3) < 3:
        advice_top3.append({"t": "현 전략 유지", "d": "해당 축은 양호해요. 지금의 규칙을 일관되게 유지하세요."})

    strategy = (
        f"단기적으로는 {top_stock_name + ' 비중 축소로 종목 리스크를 줄이고' if top_stock_concentration > 30 else '현 비중을 유지하면서'}, "
        f"{top_sector_name + ' 쏠림을 다른 업종으로 분산하는' if sector_concentration > 40 else '업종 균형을 점검하는'} 방향이 적절해요. "
        f"중기적으로는 '{label}' 성향에 맞춰 {'보유 기간을 늘려 매매 비용을 줄이고' if hold_word == '단기' else '꾸준한 적립·리밸런싱으로'} 변동성에 대응하세요. "
        "현금 비중 15% 이상을 유지하면 조정장에서 추가 매수 여력을 확보할 수 있어요."
    )

    report = {
        "label": label,
        "labelReason": label_reason,
        "disclaimer": DISCLAIMER,
        "health": {
            "breakdown": metrics.get("healthBreakdown") or {},
            "total": metrics.get("healthTotal") or 0,
            "grade": health_grade,
            "comment": health_comment,
        },
        "behavior": {"metrics": behavior, "text": behavior_text, "advice": behavior_advice, "limited": behavior_limited},
        "risk": {**risk, "text": risk_text, "advice": risk_advice},
        "returns": {**returns, "text": return_text},
        "adviceTop3": advice_top3[:3],
        "strategy": strategy,
        "input": {
            "holdings": metrics.get("holdingsCount") or 0,
            "trades": metrics.get("tradeCount") or 0,
            "watch": metrics.get("watchCount") or 0,
            "return": total_return_pct,
        },
    }
    if nickname:
        report["nickname"] = nickname
    return report
