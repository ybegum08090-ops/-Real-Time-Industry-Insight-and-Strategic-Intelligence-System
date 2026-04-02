"""
PDF Report Generator — Industry Intelligence Dashboard
========================================================
Generates a professional multi-page PDF using fpdf2.

Usage:
    pdf_bytes = generate_pdf_report(brands, product_type, brand_stats,
                                     trend_data, brand_scores, predictions,
                                     alerts, market_summary)
    # → bytes, ready for st.download_button()
"""

from fpdf import FPDF
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
#  Custom PDF class
# ─────────────────────────────────────────────────────────────────────────────

class _IndustryPDF(FPDF):
    """Custom FPDF subclass with branded header / footer."""

    _report_title = "Real-Time Industry Insights Report"

    def header(self):
        # Title
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(25, 25, 80)
        self.cell(0, 14, self._report_title, new_x="LMARGIN", new_y="NEXT", align="C")

        # Subtitle
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 170)
        self.cell(
            0, 6,
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  |  Industry Intelligence Dashboard",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )

        # Rule
        self.set_draw_color(90, 90, 200)
        self.set_line_width(0.6)
        y = self.get_y() + 3
        self.line(10, y, self.w - 10, y)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(160, 160, 160)
        self.cell(
            0, 10,
            f"Industry Intelligence Dashboard  -  Page {self.page_no()}/{{nb}}",
            align="C",
        )

    # ── Convenience methods ──────────────────────────────────────────────

    def section(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(25, 25, 80)
        self.set_fill_color(232, 232, 248)
        clean_title = str(title).encode("ascii", "replace").decode("ascii")
        self.cell(0, 10, f"  {clean_title}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def kv(self, key: str, value: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(55, 55, 110)
        clean_key = str(key).encode("ascii", "replace").decode("ascii")
        self.cell(55, 7, clean_key)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        clean_val = str(value).encode("ascii", "replace").decode("ascii")
        self.cell(0, 7, clean_val, new_x="LMARGIN", new_y="NEXT")

    def para(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        clean_text = str(text).encode("ascii", "replace").decode("ascii")
        self.multi_cell(0, 5.5, clean_text)
        self.ln(2)

    def table_header(self, widths: list[int], labels: list[str]):
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(40, 40, 90)
        self.set_text_color(255, 255, 255)
        for w, lbl in zip(widths, labels):
            self.cell(w, 8, lbl, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 8)
        self.set_text_color(30, 30, 30)

    def table_row(self, widths: list[int], values: list[str]):
        for w, v in zip(widths, values):
            v_clean = str(v).encode("ascii", "replace").decode("ascii")
            self.cell(w, 7, v_clean, border=1, align="C")
        self.ln()


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf_report(
    brands: list[str],
    product_type: str,
    brand_stats: dict[str, dict],
    trend_data: dict[str, int],
    brand_scores: dict[str, dict],
    predictions: list[dict],
    alerts: list[dict],
    market_summary: dict,
) -> bytes:
    """Build and return a professional PDF report as raw bytes."""

    pdf = _IndustryPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # 1 ── Analysis Parameters ────────────────────────────────────────────
    pdf.section("1 · Analysis Parameters")
    pdf.kv("Brands Analysed:", ", ".join(brands))
    pdf.kv("Product Category:", product_type)
    pdf.kv("Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M"))
    pdf.ln(4)

    # 2 ── Brand Comparison ───────────────────────────────────────────────
    pdf.section("2 · Brand Comparison")
    cw = [35, 27, 27, 23, 27, 27, 27]
    pdf.table_header(cw, ["Brand", "Avg Price", "Avg Rating", "Products", "Min $", "Max $", "Range"])
    for b, s in brand_stats.items():
        pdf.table_row(cw, [
            b,
            f"${s['avg_price']:.2f}" if s.get("avg_price") else "-",
            f"{s['avg_rating']:.1f}" if s.get("avg_rating") else "-",
            str(s.get("product_count", 0)),
            f"${s['min_price']:.2f}" if s.get("min_price") else "-",
            f"${s['max_price']:.2f}" if s.get("max_price") else "-",
            f"${s['price_range']:.2f}" if s.get("price_range") else "-",
        ])
    pdf.ln(4)

    # 3 ── Market Trends ──────────────────────────────────────────────────
    pdf.section("3 · Market Trends")
    if trend_data:
        tw = [70, 45, 45]
        pdf.table_header(tw, ["Brand", "Search Frequency", "Market Share %"])
        total = sum(trend_data.values()) or 1
        for b, f in sorted(trend_data.items(), key=lambda x: x[1], reverse=True):
            pdf.table_row(tw, [b, str(f), f"{f / total * 100:.1f}%"])
    else:
        pdf.para("No trend data available for this analysis.")
    pdf.ln(4)

    # 4 ── AI Market Analysis ─────────────────────────────────────────────
    pdf.section("4 · AI Market Analysis")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(25, 25, 80)
    pdf.cell(0, 7, "Market Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.para(market_summary.get("summary", "-"))

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(25, 25, 80)
    pdf.cell(0, 7, "Recommendation", new_x="LMARGIN", new_y="NEXT")
    pdf.para(market_summary.get("recommendation", "-"))

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(25, 25, 80)
    pdf.cell(0, 7, "Strategic Insight", new_x="LMARGIN", new_y="NEXT")
    pdf.para(market_summary.get("strategic_insight", "-"))

    pdf.kv("Analysis Confidence:", f"{market_summary.get('confidence', 0):.0f}%")
    pdf.ln(4)

    # 5 ── Intelligence Scores ────────────────────────────────────────────
    pdf.add_page()
    pdf.section("5 · Brand Intelligence Scores")
    sw = [32, 22, 18, 22, 22, 22, 22, 30]
    pdf.table_header(sw, ["Brand", "Score", "Grade", "Rating", "Price", "Trend", "Value", "Verdict"])
    for b, sc in brand_scores.items():
        bd = sc.get("breakdown", {})
        pdf.table_row(sw, [
            b,
            str(sc.get("total_score", 0)),
            sc.get("grade", "-"),
            str(bd.get("rating", {}).get("score", 0)),
            str(bd.get("price", {}).get("score", 0)),
            str(bd.get("trend", {}).get("score", 0)),
            str(bd.get("value", {}).get("score", 0)),
            "Leader" if sc.get("total_score", 0) >= 70 else "Solid" if sc.get("total_score", 0) >= 45 else "Weak",
        ])
    pdf.ln(4)

    # 6 ── Predictions ────────────────────────────────────────────────────
    pdf.section("6 · Market Predictions")
    if predictions:
        pw = [40, 30, 40, 40, 40]
        pdf.table_header(pw, ["Brand", "Pred Score", "Outlook", "Intel Score", "Trend %"])
        for p in predictions:
            outlook_clean = p.get("outlook", "").encode("ascii", "replace").decode("ascii")
            pdf.table_row(pw, [
                p["brand"],
                str(p["prediction_score"]),
                outlook_clean,
                str(p["intelligence_score"]),
                f"{p['trend_strength']:.0f}%",
            ])
    else:
        pdf.para("No prediction data available.")
    pdf.ln(4)

    # 7 ── Smart Alerts ───────────────────────────────────────────────────
    pdf.section("7 · Smart Insight Alerts")
    if alerts:
        for a in alerts:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(55, 55, 110)
            title_clean = a.get("title", "").encode("ascii", "replace").decode("ascii")
            pdf.cell(0, 7, title_clean, new_x="LMARGIN", new_y="NEXT")
            msg_clean = a.get("message", "").encode("ascii", "replace").decode("ascii")
            pdf.para(msg_clean)
    else:
        pdf.para("No alerts generated.")

    # ── Output ───────────────────────────────────────────────────────────
    return bytes(pdf.output())
