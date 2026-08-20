import json
import os
import re
from collections import defaultdict
from datetime import date, datetime
from statistics import mean
from typing import Optional
from uuid import uuid4
 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
 
app = FastAPI(title="Financer Dashboard API", version="1.0.0")
 
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
extra_origin = os.environ.get("FRONTEND_ORIGIN")
if extra_origin:
    ALLOWED_ORIGINS.append(extra_origin)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "transactions.json")
 
CATEGORIES = [
    "Groceries",
    "Restaurants",
    "Transportation",
    "Subscriptions",
    "Shopping",
    "Entertainment",
    "Utilities",
    "Healthcare",
    "Travel",
    "Other",
]
 
 
class Transaction(BaseModel):
    id: str
    date: date
    merchant: str
    category: str
    amount: float
 
 
class TransactionCreate(BaseModel):
    category: str = Field(min_length=1, max_length=40)
    merchant: str = Field(min_length=1, max_length=80)
    amount: float = Field(gt=0, le=1_000_000)
    date: Optional[str]= None #string in ISO format 
 
    @field_validator("category", "merchant", mode="before")
    @classmethod
    def strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v
 
 
def parse_transaction_date(raw: Optional[str]) -> date:
    if not raw:
        return date.today()
    try:
        return date.fromisoformat(raw.strip())
    except ValueError:
        return date.today()
 
 
class QuestionRequest(BaseModel):
    question: str
 
 
def load_transactions() -> list[Transaction]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            raw = json.load(f)
        return [Transaction(**item) for item in raw]
    except Exception:
        # handling read/parse errors
        return []
 
 
def save_transactions(transactions: list[Transaction]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump([t.model_dump(mode="json") for t in transactions], f, indent=2, default=str)
 
 
TRANSACTIONS: list[Transaction] = load_transactions()
 
# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
 
def month_key(d: date) -> str:
    return d.strftime("%Y-%m")
 
 
def monthly_totals():
    totals = defaultdict(float)
    for t in TRANSACTIONS:
        totals[month_key(t.date)] += t.amount
    ordered = sorted(totals.items())
    return [{"month": k, "total": round(v, 2)} for k, v in ordered]
 
 
def category_totals(month: Optional[str]):
    if not month:
        return []
    totals = defaultdict(float)
    for t in TRANSACTIONS:
        if month_key(t.date) == month:
            totals[t.category] += t.amount
    return [
        {"category": k, "total": round(v, 2)}
        for k, v in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]
 
 
def forecast_next_month():
    totals = monthly_totals()
    vals = [m["total"] for m in totals]
    return round(mean(vals), 2) if vals else 0.0
 
 
def spending_delta_explanation():
    totals = monthly_totals()
    if len(totals) == 0:
        return "No expenses yet. Add a few below to see monthly insights."
    if len(totals) < 2:
        return "Not enough data yet to compare months. Add expenses from another month to unlock this."
    current, previous = totals[-1], totals[-2]
    diff = round(current["total"] - previous["total"], 2)
    current_cats = {c["category"]: c["total"] for c in category_totals(current["month"])}
    prev_cats = {c["category"]: c["total"] for c in category_totals(previous["month"])}
    deltas = []
    for cat in set(current_cats) | set(prev_cats):
        deltas.append((cat, round(current_cats.get(cat, 0) - prev_cats.get(cat, 0), 2)))
    deltas.sort(key=lambda x: abs(x[1]), reverse=True)
    top = [d for d in deltas if d[1] > 0][:2]
    if diff <= 0:
        return f"You spent ${abs(diff):.2f} less than last month, mainly because higher categories did not repeat."
    if not top:
        return f"You spent ${diff:.2f} more than last month."
    reasons = ", ".join([f"{cat} increased by ${amt:.2f}" for cat, amt in top])
    return f"You spent ${diff:.2f} more than last month because {reasons}."
 
 
# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
 
 
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
 
 
@app.get("/categories")
def get_categories():
    return CATEGORIES
 
 
@app.get("/dashboard")
def dashboard():
    totals = monthly_totals()
    current_month = totals[-1]["month"] if totals else None
    return {
        "monthly_totals": totals,
        "current_month": current_month,
        "category_breakdown": category_totals(current_month),
        "forecast_next_month": forecast_next_month(),
        "insight": spending_delta_explanation(),
        "transactions": [t.model_dump() for t in sorted(TRANSACTIONS, key=lambda x: x.date, reverse=True)],
    }
 
 
@app.get("/transactions")
def list_transactions():
    return [t.model_dump() for t in sorted(TRANSACTIONS, key=lambda x: x.date, reverse=True)]
 
 
@app.post("/transactions")
def add_transaction(payload: TransactionCreate):
    txn = Transaction(
        id=f"t{uuid4().hex[:10]}",
        date=parse_transaction_date(payload.date),
        merchant=payload.merchant.strip(),
        category=payload.category.strip(),
        amount=round(payload.amount, 2),
    )
    TRANSACTIONS.append(txn)
    save_transactions(TRANSACTIONS)
    return dashboard()
 
 
@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: str):
    global TRANSACTIONS
    before = len(TRANSACTIONS)
    TRANSACTIONS = [t for t in TRANSACTIONS if t.id != transaction_id]
    if len(TRANSACTIONS) == before:
        raise HTTPException(status_code=404, detail="Transaction not found")
    save_transactions(TRANSACTIONS)
    return dashboard()
 
 
MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
 
 
def _find_month_mention(q: str, dashboard_data: dict) -> Optional[str]:
    """Look for an explicit month reference (e.g. '2026-06' or 'june 2026' or
    just 'june') in the question and return it in 'YYYY-MM' form, but only if
    we actually have data for that month."""
    known_months = {m["month"] for m in dashboard_data["monthly_totals"]}
 
    match = re.search(r"(20\d{2})-(0[1-9]|1[0-2])", q)
    if match and match.group(0) in known_months:
        return match.group(0)
 
    for name, num in MONTH_NAMES.items():
        if re.search(rf"\b{name}\b", q):
            year_match = re.search(r"20\d{2}", q)
            if year_match:
                candidate = f"{year_match.group(0)}-{num:02d}"
                if candidate in known_months:
                    return candidate
            else:
                # No year given: match any known month with that number
                matches = [m for m in known_months if m.endswith(f"-{num:02d}")]
                if len(matches) == 1:
                    return matches[0]
    return None
 
 
def _find_category_mention(q: str) -> Optional[str]:
    seen = {}
    for t in TRANSACTIONS:
        seen.setdefault(t.category.lower(), t.category)
    for key in sorted(seen, key=len, reverse=True):
        if key in q:
            return seen[key]
    return None
 
 
def _find_merchant_mention(q: str) -> Optional[str]:
    seen = {}
    for t in TRANSACTIONS:
        seen.setdefault(t.merchant.lower(), t.merchant)
    for key in sorted(seen, key=len, reverse=True):
        if key in q:
            return seen[key]
    return None
 
 
def _category_total(category: str) -> tuple[float, int]:
    matches = [t for t in TRANSACTIONS if t.category.lower() == category.lower()]
    return round(sum(t.amount for t in matches), 2), len(matches)
 
 
def _merchant_total(merchant: str) -> tuple[float, int]:
    matches = [t for t in TRANSACTIONS if t.merchant.lower() == merchant.lower()]
    return round(sum(t.amount for t in matches), 2), len(matches)
 
 
def rule_based_answer(q: str, dashboard_data: dict) -> str:
    if not TRANSACTIONS:
        return "You haven't added any expenses yet. Add a few below and ask again!"
    if "spend" in q or "spent" in q:
        category = _find_category_mention(q)
        merchant = _find_merchant_mention(q)
        if category:
            total, count = _category_total(category)
            return f"You spent ${total:.2f} on {category} across {count} transaction{'s' if count != 1 else ''}."
        if merchant:
            total, count = _merchant_total(merchant)
            return f"You spent ${total:.2f} at {merchant} across {count} transaction{'s' if count != 1 else ''}."
 
    if re.search(r"(total|overall|altogether|all[- ]time)", q) and ("spend" in q or "spent" in q):
        total = round(sum(t.amount for t in TRANSACTIONS), 2)
        return f"You've spent ${total:.2f} in total across {len(TRANSACTIONS)} transactions."
 
    if any(p in q for p in ["why did i spend more", "why did i spend less", "spending change", "spend more this month", "spend less this month"]):
        return dashboard_data["insight"]
 
    comparison_phrases = ["compared to last month", "vs last month", "versus last month", "than last month"]
    if (("this month" in q and "last month" in q) or any(p in q for p in comparison_phrases)) and (
        "spend" in q or "spent" in q or "more" in q or "less" in q
    ):
        totals = dashboard_data["monthly_totals"]
        if len(totals) >= 2:
            current, previous = totals[-1], totals[-2]
            diff = round(current["total"] - previous["total"], 2)
            if diff > 0:
                return f"You've spent ${diff:.2f} more this month ({current['month']}) than last month ({previous['month']}): ${current['total']:.2f} vs ${previous['total']:.2f}."
            if diff < 0:
                return f"You've spent ${abs(diff):.2f} less this month ({current['month']}) than last month ({previous['month']}): ${current['total']:.2f} vs ${previous['total']:.2f}."
            return f"You've spent the same so far this month ({current['month']}) as last month ({previous['month']}): ${current['total']:.2f}."
        return "I don't have a full previous month of data yet to compare."
 
    if ("spend" in q or "spent" in q):
        mentioned_month = _find_month_mention(q, dashboard_data)
        if mentioned_month:
            total = next((m["total"] for m in dashboard_data["monthly_totals"] if m["month"] == mentioned_month), 0)
            return f"You spent ${total:.2f} in {mentioned_month}."
 
    if "this month" in q and ("spend" in q or "spent" in q):
        current_month = dashboard_data["current_month"]
        total = next((m["total"] for m in dashboard_data["monthly_totals"] if m["month"] == current_month), 0)
        return f"You've spent ${total:.2f} so far in {current_month}."
 
    if "last month" in q and ("spend" in q or "spent" in q):
        totals = dashboard_data["monthly_totals"]
        if len(totals) >= 2:
            prev = totals[-2]
            return f"You spent ${prev['total']:.2f} in {prev['month']}."
        return "I don't have a full previous month of data yet."
 
    if "forecast" in q or "next month" in q or "predict" in q:
        return f"Based on your history, I'd estimate about ${dashboard_data['forecast_next_month']:.2f} in spending next month."
 
    if any(p in q for p in ["biggest expense", "spend the most", "top category", "highest category", "spending the most", "largest expense"]):
        mentioned_month = _find_month_mention(q, dashboard_data)
        if mentioned_month:
            breakdown = category_totals(mentioned_month)
            label = f" in {mentioned_month}"
        else:
            breakdown = dashboard_data["category_breakdown"]
            label = " this month"
        if breakdown:
            top = breakdown[0]
            return f"Your biggest spending category{label} is {top['category']} at ${top['total']:.2f}."
        return f"I don't have any spending data{label if mentioned_month else ''} to find a top category."

    save_match = re.search(r"save\D{0,6}?\$?\s?([\d,]+(?:\.\d+)?)", q)
    if save_match:
        goal = float(save_match.group(1).replace(",", ""))
        weekly = round(goal / 4, 2)
        breakdown = dashboard_data["category_breakdown"]
        tip = ""
        if breakdown:
            top = breakdown[:2]
            names = " and ".join(c["category"] for c in top)
            tip = f" Start by trimming {names} — your highest categories this month."
        return f"To save ${goal:,.2f} next month, set aside about ${weekly:,.2f} per week.{tip}"
 
    if "average" in q and ("transaction" in q or "purchase" in q or "spend" in q):
        avg = mean(t.amount for t in TRANSACTIONS)
        return f"Your average transaction is ${avg:.2f} across {len(TRANSACTIONS)} transactions."
 
    if "how many transactions" in q or "number of transactions" in q:
        return f"You have {len(TRANSACTIONS)} transactions recorded."
 
    return (
        "I can answer things like 'How much did I spend on groceries?', 'What's my biggest expense?', "
        "'How can I save $300?', or 'What's my forecast for next month?'. "
    )
 
 
def ai_answer_gemini(question: str, dashboard_data: dict) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
 
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        context = (
            "You are a personal finance assistant. Answer the user's question using ONLY "
            f"this transaction summary JSON, be concise (2-4 sentences), and use dollar amounts.\n\n"
            f"Summary: {dashboard_data}\n\nQuestion: {question}"
        )
        response = model.generate_content(context)
        return response.text.strip()
    except Exception:
        return None
 
 
def ai_answer_claude(question: str, dashboard_data: dict) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
 
        client = anthropic.Anthropic(api_key=api_key)
        context = (
            "You are a personal finance assistant. Answer the user's question using ONLY "
            f"this transaction summary JSON, be concise (2-4 sentences), and use dollar amounts.\n\n"
            f"Summary: {dashboard_data}\n\nQuestion: {question}"
        )
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": context}],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        return text.strip() or None
    except Exception:
        return None
 
 
@app.post("/ask")
def ask_question(payload: QuestionRequest):
    q = payload.question.lower()
    dashboard_data = dashboard()
 
    ai_response = ai_answer_claude(payload.question, dashboard_data)
    if ai_response:
        return {"answer": ai_response, "source": "claude"}
 
    ai_response = ai_answer_gemini(payload.question, dashboard_data)
    if ai_response:
        return {"answer": ai_response, "source": "gemini"}
 
    return {"answer": rule_based_answer(q, dashboard_data), "source": "rules"}