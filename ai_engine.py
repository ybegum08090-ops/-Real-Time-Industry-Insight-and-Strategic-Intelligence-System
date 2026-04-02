"""
AI Engine — Industry Intelligence Dashboard
=============================================
Pure-Python analysis layer: scoring, momentum, predictions, alerts, summaries.
No external ML dependencies — deterministic, explainable, and fast.
"""

import re
from collections import Counter

def parse_price(raw) -> float | None:
    """'$149.99' → 149.99  |  None / 'N/A' → None"""
    if not raw or str(raw).strip().upper() == "N/A":
        return None
    cleaned = re.sub(r"[^\d.]", "", str(raw))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def compute_stats(products: list) -> dict:
    """Aggregate stats from a list of product dicts."""
    prices, ratings, reviews_list = [], [], []

    for p in products:
        pv = parse_price(p.get("price"))
        if pv is not None:
            prices.append(pv)

        rv = p.get("rating")
        if rv is not None:
            try:
                ratings.append(float(rv))
            except (ValueError, TypeError):
                pass

        rev = p.get("reviews", 0)
        if rev:
            try:
                reviews_list.append(int(rev))
            except (ValueError, TypeError):
                pass

    avg_price = sum(prices) / len(prices) if prices else None
    avg_rating = sum(ratings) / len(ratings) if ratings else None

    return {
        "avg_price": avg_price,
        "avg_rating": avg_rating,
        "total_reviews": sum(reviews_list),
        "product_count": len(products),
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "price_range": (max(prices) - min(prices)) if len(prices) >= 2 else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Brand Intelligence Score (0-100)
# ─────────────────────────────────────────────────────────────────────────────

def _grade(score: float) -> str:
    for threshold, label in [
        (85, "A+"), (75, "A"), (65, "B+"), (55, "B"),
        (45, "C+"), (35, "C"), (25, "D"),
    ]:
        if score >= threshold:
            return label
    return "F"


def compute_brand_intelligence_score(
    stats: dict,
    trend_frequency: int = 0,
    max_trend: int = 1,
) -> dict:
    """
    Score = Rating(35) + Price(25) + Trend(25) + Value(15)
    Returns total_score, grade, and per-component breakdown with explanations.
    """
    bd: dict[str, dict] = {}

    # ── Rating (0-35) ────────────────────────────────────────────────────
    ar = stats.get("avg_rating")
    if ar is not None:
        rs = (ar / 5.0) * 35
        bd["rating"] = {
            "score": round(rs, 1), "max": 35, "value": ar,
            "explanation": f"Avg rating {ar:.1f}/5.0 → {rs:.1f}/35 pts",
        }
    else:
        rs = 0
        bd["rating"] = {
            "score": 0, "max": 35, "value": None,
            "explanation": "No rating data (0/35 pts)",
        }

    # ── Price competitiveness (0-25) ─────────────────────────────────────
    ap = stats.get("avg_price")
    if ap and ap > 0:
        ps = max(0.0, min(25.0, (1 - ap / 500) * 25))
        tag = "competitive" if ps > 15 else "premium"
        bd["price"] = {
            "score": round(ps, 1), "max": 25, "value": ap,
            "explanation": f"Avg ${ap:.2f} — {tag} pricing ({ps:.1f}/25 pts)",
        }
    else:
        ps = 0
        bd["price"] = {
            "score": 0, "max": 25, "value": None,
            "explanation": "No price data (0/25 pts)",
        }

    # ── Trend / Market Presence (0-25) ───────────────────────────────────
    if max_trend > 0 and trend_frequency > 0:
        ts = (trend_frequency / max_trend) * 25
        bd["trend"] = {
            "score": round(ts, 1), "max": 25, "value": trend_frequency,
            "explanation": f"{trend_frequency} trend mentions ({ts:.1f}/25 pts)",
        }
    else:
        ts = 0
        bd["trend"] = {
            "score": 0, "max": 25, "value": 0,
            "explanation": "No trend data (0/25 pts)",
        }

    # ── Value for money (0-15) ───────────────────────────────────────────
    if ar and ap and ap > 0:
        ratio = ar / ap
        vs = min(15.0, ratio * 300)
        tag = "excellent" if vs > 10 else "moderate"
        bd["value"] = {
            "score": round(vs, 1), "max": 15, "value": round(ratio, 5),
            "explanation": f"Rating/Price = {ratio:.5f} — {tag} value ({vs:.1f}/15 pts)",
        }
    else:
        vs = 0
        bd["value"] = {
            "score": 0, "max": 15, "value": None,
            "explanation": "Insufficient data (0/15 pts)",
        }

    total = rs + ps + ts + vs
    return {"total_score": round(total, 1), "grade": _grade(total), "breakdown": bd}


# ─────────────────────────────────────────────────────────────────────────────
#  Market Momentum
# ─────────────────────────────────────────────────────────────────────────────

def detect_market_momentum(brand_frequencies: dict) -> list[dict]:
    """Label each brand as Rising / Stable / Declining based on frequency."""
    if not brand_frequencies:
        return []

    vals = list(brand_frequencies.values())
    avg = sum(vals) / len(vals)
    mx = max(vals) if vals else 1

    rows = []
    for brand, freq in brand_frequencies.items():
        if freq > avg * 1.3:
            status, momentum = "🚀 Rising", "high"
        elif freq >= avg * 0.8:
            status, momentum = "➡️ Stable", "stable"
        else:
            status, momentum = "📉 Declining", "low"
        rows.append({
            "brand": brand,
            "frequency": freq,
            "status": status,
            "momentum": momentum,
            "strength": round((freq / mx) * 100, 1) if mx else 0,
        })
    rows.sort(key=lambda x: x["frequency"], reverse=True)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
#  Predictions
# ─────────────────────────────────────────────────────────────────────────────

def generate_predictions(
    brand_scores: dict[str, dict],
    trend_data: dict[str, int],
) -> list[dict]:
    """
    Predict future leading brands.
    Prediction = 60 % intelligence score + 40 % trend momentum.
    """
    if not brand_scores:
        return []

    mx = max(trend_data.values()) if trend_data else 1
    preds = []
    for brand, sd in brand_scores.items():
        ts = sd.get("total_score", 0)
        tf = trend_data.get(brand, 0)
        tn = (tf / mx) * 100 if mx else 0
        ps = ts * 0.6 + tn * 0.4
        if ps > 70:
            outlook = "🟢 Strong Growth Expected"
        elif ps > 50:
            outlook = "🟡 Moderate Growth"
        elif ps > 30:
            outlook = "🟠 Uncertain"
        else:
            outlook = "🔴 Potential Decline"
        preds.append({
            "brand": brand,
            "prediction_score": round(ps, 1),
            "outlook": outlook,
            "intelligence_score": ts,
            "trend_strength": round(tn, 1),
        })
    preds.sort(key=lambda x: x["prediction_score"], reverse=True)
    return preds


# ─────────────────────────────────────────────────────────────────────────────
#  Smart Alerts
# ─────────────────────────────────────────────────────────────────────────────

def generate_smart_alerts(
    all_brand_data: dict[str, list],
    brand_stats: dict[str, dict],
) -> list[dict]:
    """Detect overpriced, best deals, hype-vs-quality, premium quality, price leader."""
    alerts: list[dict] = []
    price_pairs = [(b, s["avg_price"]) for b, s in brand_stats.items() if s.get("avg_price")]
    rating_pairs = [(b, s["avg_rating"]) for b, s in brand_stats.items() if s.get("avg_rating")]

    if not price_pairs and not rating_pairs:
        return [{"type": "info", "icon": "ℹ️", "title": "Insufficient Data",
                 "message": "Not enough data to generate alerts.", "severity": "low"}]

    avg_p = sum(v for _, v in price_pairs) / len(price_pairs) if price_pairs else 0
    avg_r = sum(v for _, v in rating_pairs) / len(rating_pairs) if rating_pairs else 0

    for brand, s in brand_stats.items():
        bp, br = s.get("avg_price"), s.get("avg_rating")

        if bp and br and bp < avg_p * 0.85 and br > avg_r:
            alerts.append({
                "type": "deal", "icon": "💎", "severity": "positive", "brand": brand,
                "title": f"Best Deal — {brand}",
                "message": (
                    f"{brand} delivers outstanding value: avg ${bp:.2f} "
                    f"(below market ${avg_p:.2f}) with {br:.1f}/5 rating."
                ),
            })
        if bp and br and bp > avg_p * 1.15 and br < avg_r:
            alerts.append({
                "type": "overpriced", "icon": "⚠️", "severity": "warning", "brand": brand,
                "title": f"Overpriced — {brand}",
                "message": (
                    f"{brand} costs ${bp:.2f} (above ${avg_p:.2f} avg) "
                    f"with below-average rating {br:.1f}/5."
                ),
            })
        if br and br < 3.5 and s.get("total_reviews", 0) > 50:
            alerts.append({
                "type": "hype", "icon": "🔥", "severity": "caution", "brand": brand,
                "title": f"Hype vs Quality — {brand}",
                "message": (
                    f"{brand} has high visibility but low rating ({br:.1f}/5). "
                    f"May be hype-driven."
                ),
            })
        if br and br >= 4.5:
            alerts.append({
                "type": "premium", "icon": "⭐", "severity": "positive", "brand": brand,
                "title": f"Premium Quality — {brand}",
                "message": f"{brand} has exceptional quality with {br:.1f}/5 average rating.",
            })

    if price_pairs:
        cheapest = min(price_pairs, key=lambda x: x[1])
        alerts.append({
            "type": "price_leader", "icon": "🏷️", "severity": "info", "brand": cheapest[0],
            "title": f"Price Leader — {cheapest[0]}",
            "message": f"{cheapest[0]} offers the lowest avg price at ${cheapest[1]:.2f}.",
        })

    if not alerts:
        alerts.append({
            "type": "info", "icon": "✅", "severity": "positive",
            "title": "All Brands Performing Well",
            "message": "No anomalies detected across compared brands.",
        })

    return alerts


# ─────────────────────────────────────────────────────────────────────────────
#  AI Market Summary
# ─────────────────────────────────────────────────────────────────────────────

def generate_market_summary(
    brand_stats: dict,
    trend_data: dict,
    brand_scores: dict,
    predictions: list,
    alerts: list,
) -> dict:
    """Narrative market analysis with recommendation and strategic insight."""
    if not brand_stats:
        return {
            "summary": "No data available.",
            "recommendation": "N/A",
            "strategic_insight": "N/A",
            "confidence": 0,
            "best_brand": None,
            "best_score": None,
        }

    names = list(brand_stats.keys())
    best = max(brand_scores.items(), key=lambda x: x[1].get("total_score", 0)) if brand_scores else None
    top_trend = max(trend_data.items(), key=lambda x: x[1]) if trend_data else None

    # ── Summary ──────────────────────────────────────────────────────────
    parts = [f"Analysed {len(names)} brand{'s' if len(names) > 1 else ''}: {', '.join(names)}."]
    prices = {b: s["avg_price"] for b, s in brand_stats.items() if s.get("avg_price")}
    if prices:
        lo = min(prices, key=prices.get)
        hi = max(prices, key=prices.get)
        parts.append(f"Price range: {lo} (${prices[lo]:.2f}) to {hi} (${prices[hi]:.2f}).")
    ratings = {b: s["avg_rating"] for b, s in brand_stats.items() if s.get("avg_rating")}
    if ratings:
        top_r = max(ratings, key=ratings.get)
        parts.append(f"{top_r} leads satisfaction at {ratings[top_r]:.1f}/5.")
    summary = " ".join(parts)

    # ── Recommendation ───────────────────────────────────────────────────
    if best:
        recommendation = (
            f"Top pick: {best[0]} — Intelligence Score {best[1]['total_score']}/100 "
            f"(Grade {best[1]['grade']}). It balances pricing, quality, and market "
            f"presence most effectively among the analysed brands."
        )
    else:
        recommendation = "Insufficient data for a recommendation."

    # ── Strategic insight ────────────────────────────────────────────────
    ins = []
    warns = [a for a in alerts if a.get("severity") in ("warning", "caution")]
    if predictions and predictions[0].get("prediction_score", 0) > 60:
        ins.append(f"{predictions[0]['brand']} has the strongest growth trajectory.")
    if warns:
        flagged = list({a.get("brand", "?") for a in warns})
        ins.append(f"Caution advised for {', '.join(flagged)}.")
    if top_trend:
        ins.append(f"{top_trend[0]} dominates search trends ({top_trend[1]} mentions).")
    strategic = " ".join(ins) if ins else "Market is balanced across analysed brands."

    dp = sum(1 for s in brand_stats.values() if s.get("avg_price")) + \
         sum(1 for s in brand_stats.values() if s.get("avg_rating"))
    confidence = (dp / (len(names) * 2)) * 100 if names else 0

    return {
        "summary": summary,
        "recommendation": recommendation,
        "strategic_insight": strategic,
        "confidence": round(confidence, 1),
        "best_brand": best[0] if best else None,
        "best_score": best[1] if best else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Explainable AI (XAI)
# ─────────────────────────────────────────────────────────────────────────────

def explain_decision(score_data: dict, brand_name: str) -> str:
    """Human-readable explanation of a brand's intelligence score."""
    bd = score_data.get("breakdown", {})
    total = score_data.get("total_score", 0)
    grade = score_data.get("grade", "N/A")

    lines = [f"### Why {brand_name} scored {total}/100 (Grade: {grade})\n"]

    for label, key in [
        ("Rating Quality", "rating"),
        ("Price Competitiveness", "price"),
        ("Market Presence", "trend"),
        ("Value for Money", "value"),
    ]:
        d = bd.get(key, {})
        sc = d.get("score", 0)
        mx = d.get("max", 1)
        filled = int((sc / mx) * 10) if mx else 0
        bar = "█" * filled + "░" * (10 - filled)
        lines.append(f"**{label}** {bar} `{sc}/{mx}`")
        lines.append(f"> {d.get('explanation', 'No data')}\n")

    if total >= 70:
        lines.append(f"✅ **{brand_name}** is a strong market performer.")
    elif total >= 45:
        lines.append(f"ℹ️ **{brand_name}** shows moderate performance with room to grow.")
    else:
        lines.append(f"⚠️ **{brand_name}** faces challenges in pricing, quality, or visibility.")

    return "\n".join(lines)
