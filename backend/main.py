from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sqlite3
import os
import requests
import yfinance as yf
from fredapi import Fred
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .advisor import get_rule_based_recommendation, generate_ai_recommendation, search_funds, get_fund_history, init_recommendations_db


# Load environment variables from .env file
load_dotenv()

app = FastAPI()


# Enable CORS -> Frontend can talk to Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
init_recommendations_db()

# Models
class RecommendationRequest(BaseModel):
    age: int
    income: float
    profession: str
    region: str
    goal: str
    api_key: str = None 

# --- Endpoints ---

@app.get("/api/health")
def read_root():
    return {"status": "Finance AI API is running"}


@app.post("/api/recommendation")
def get_recommendation(req: RecommendationRequest):
    # 1. Rule Based
    rule_res = get_rule_based_recommendation(req.age, req.income, req.goal)
    if rule_res:
        return {**rule_res, "source": "Rule Engine"}
    
    # 2. AI Based
    api_key = os.getenv("GEMINI_API_KEY") or req.api_key
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key missing")
        
    ai_res = generate_ai_recommendation(req.age, req.income, req.profession, req.region, req.goal, api_key)
    return {**ai_res, "source": "Gemini AI"}

@app.get("/api/funds/search")
def search_mutual_funds(q: str):
    return search_funds(q)

@app.get("/api/funds/{scheme_code}")
def get_mutual_fund_history(scheme_code: str):
    return get_fund_history(scheme_code)


@app.get("/api/news")
def get_financial_news(q: str = "finance", api_key: str = None):
    # Use env var or passed key
    key = os.getenv("NEWS_API_KEY") or api_key
    if not key:
        raise HTTPException(status_code=400, detail="News API Key missing")
        
    url = f"https://newsapi.org/v2/everything?q={q}&sortBy=publishedAt&apiKey={key}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json().get("articles", [])[:10]
        return []
    except:
        return []

@app.get("/api/market/history")
def get_market_history(symbol: str = "AAPL", period: str = "1y"):
    try:
        data = yf.download(symbol, period=period)
        if data.empty:
            return []
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Convert to list of dicts: [{Date: '...', Close: 123}, ...]
        result = []
        for _, row in data.iterrows():
            result.append({
                "date": row['Date'].strftime('%Y-%m-%d'),
                "close": row['Close']
            })
        return result
    except Exception as e:
        print(f"Market Error: {e}")
        return []

@app.get("/api/economic/data")
def get_fred_data(series_id: str = "UNRATE", api_key: str = None):
    key = os.getenv("FRED_API_KEY") or api_key
    if not key:
         raise HTTPException(status_code=400, detail="FRED API Key missing")
    
    try:
        fred = Fred(api_key=key)
        data = fred.get_series(series_id)
        # Convert to list of dicts
        result = []
        # Fred returns a Series with DateTime index
        for date, value in data.tail(20).items():
             result.append({"date": date.strftime('%Y-%m-%d'), "value": value})
        return result
    except:
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Serve Frontend (Must be last to avoid overriding API routes)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")


