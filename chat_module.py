"""
AI Chat Analyst — Industry Intelligence
=========================================
Rule-based, deterministic NLP engine to interpret natural language queries
and generate explainable responses using pre-computed MCP market data. No LLM APIs used.
"""

from ai_engine import explain_decision

# ── Intent keywords ──────────────────────────────────────────────────────────

INTENTS = {
    "best_brand": ["best", "top", "leader", "number one", "highest ranked", "winner", "rank 1"],
    "overpriced": ["overpriced", "expensive", "costly", "rip off", "not worth", "worst deal"],
    "deal": ["deal", "cheap", "value", "bargain", "affordable", "lowest price", "price leader"],
    "trend": ["trend", "popular", "talked about", "famous", "mentioned", "market share", "search"],
    "prediction": ["predict", "future", "growth", "next", "tomorrow", "forecast", "trajectory"],
    "explanation": ["why", "explain", "reason", "how come", "justify", "because"],
    "comparison": ["compare", "vs", "versus", "difference", "better than"],
    "sales": ["sales", "sold", "revenue", "profit", "how many"],
}

class ChatAnalyst:
    def __init__(self, brands, brand_stats, trend_data, brand_scores, predictions, alerts, market_summary):
        self.brands = [b.lower() for b in brands]
        self.original_brands = {b.lower(): b for b in brands}
        self.stats = brand_stats
        self.trends = trend_data
        self.scores = brand_scores
        self.preds = predictions
        self.alerts = alerts
        self.summary = market_summary
        self.confidence = "High"

    def parse_intent(self, query: str) -> str:
        q = query.lower()
        for intent, keywords in INTENTS.items():
            if any(k in q for k in keywords):
                return intent
        return "general_summary"

    def extract_brand(self, query: str) -> str | None:
        q = query.lower()
        for b in self.brands:
            if b in q:
                return self.original_brands.get(b)
        return None

    def respond(self, query: str, context: dict = None) -> tuple[str, dict]:
        """Returns (response_text, new_context)"""
        if context is None:
            context = {}
            
        intent = self.parse_intent(query)
        target_brand = self.extract_brand(query) or context.get("last_brand")
        
        # Guard clause for hallucination-prone queries
        if intent == "sales":
            self.confidence = "High"
            b_text = f" for {target_brand}" if target_brand else ""
            return f"Sales data{b_text} is not available in real-time from public search sources. However, based on current search trends and shopping metrics, I can evaluate their relative momentum or value.", context
            
        if intent == "explanation":
            self.confidence = "High"
            if not target_brand:
                best_b = self.summary.get("best_brand")
                if best_b:
                    target_brand = best_b
                else:
                    return "Could you specify which brand's performance you'd like me to explain?", context
            
            exp = explain_decision(self.scores.get(target_brand, {}), target_brand)
            context["last_brand"] = target_brand
            return f"{exp}", context

        if intent == "best_brand":
            self.confidence = "High"
            best_b = self.summary.get("best_brand")
            if not best_b:
                return "Insufficient data to determine a top brand right now.", context
                
            score = self.scores.get(best_b, {}).get("total_score")
            grade = self.scores.get(best_b, {}).get("grade")
            context["last_brand"] = best_b
            return f"The strongest market performer is **{best_b}** with an Intelligence Score of **{score}/100** (Grade {grade}). It perfectly balances pricing, quality, and market presence. If you'd like to know the exact formula, just ask 'Why is {best_b} the best?'.", context

        if intent == "overpriced":
            self.confidence = "High"
            over = [a for a in self.alerts if a.get("type") == "overpriced"]
            if over:
                res = "\n".join([f"- **{a['brand']}**: {a['message']}" for a in over])
                context["last_brand"] = over[0]['brand']
                return f"I have detected the following overpriced or underperforming brands:\n{res}", context
            return "Based on the current real-time data, none of the analyzed brands are mathematically flagged as overpriced or 'hype' right now.", context

        if intent == "deal":
            self.confidence = "High"
            deals = [a for a in self.alerts if a.get("type") in ("deal", "price_leader")]
            if deals:
                res = "\n".join([f"- **{a['brand']}**: {a['message']}" for a in deals])
                return f"Here are the most mathematically sound deals on the market right now:\n{res}", context
            return "I couldn't detect any standout deals right now. Pricing is highly consistent across competitors.", context

        if intent == "trend":
            self.confidence = "High"
            if self.trends:
                top = max(self.trends.items(), key=lambda x: x[1])
                context["last_brand"] = top[0]
                return f"**{top[0]}** is dominating market mindshare right now with {top[1]} major organic search mentions across the web.", context
            return "Organic search volume data is currently unavailable.", context
            
        if intent == "prediction":
            self.confidence = "Medium"
            if self.preds:
                top_pred = self.preds[0]
                context["last_brand"] = top_pred["brand"]
                return f"The algorithm predicts **{top_pred['brand']}** will lead moving forward. Outlook: **{top_pred['outlook']}**. This is driven by its Prediction Score of {top_pred['prediction_score']}/100.", context
            return "Not enough historical momentum data to run market predictions.", context
            
        if intent == "comparison":
            self.confidence = "High"
            sorted_brands = sorted(self.scores.keys(), key=lambda x: self.scores[x].get("total_score", 0), reverse=True)
            if len(sorted_brands) >= 2:
                b1, b2 = sorted_brands[0], sorted_brands[1]
                s1, s2 = self.scores[b1]['total_score'], self.scores[b2]['total_score']
                return f"Comparing the top two players: **{b1}** (Score: {s1}/100) vs **{b2}** (Score: {s2}/100).\n{b1} has stronger metrics right now.", context
            return "Provide more brands to generate a comparison view.", context
            
        # Default fallback
        self.confidence = "Medium"
        return f"{self.summary.get('summary', 'I analyzed the market.')} {self.summary.get('strategic_insight', 'Please ask me a specific question about rankings, prices, or trends.')}", context
