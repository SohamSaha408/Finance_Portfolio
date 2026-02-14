import google.generativeai as genai
import re
import json
import sqlite3
import hashlib
from datetime import datetime
import requests
import os

# Database Path - simplified for the new structure
DB_PATH = 'users.db'

# Initialize Database
def init_recommendations_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS recommendations
                     (id TEXT PRIMARY KEY, 
                      user_id INTEGER, 
                      profile_hash TEXT, 
                      advice_text TEXT, 
                      allocation TEXT, 
                      created_at TIMESTAMP)''')
        conn.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")
    finally:
        conn.close()

def get_profile_hash(age, income, profession, region, goal):
    """Creates a unique hash for a user profile to cache results."""
    profile_str = f"{age}-{income}-{profession}-{region}-{goal}"
    return hashlib.md5(profile_str.encode()).hexdigest()

def get_rule_based_recommendation(age, income, goal):
    """Returns a fallback recommendation based on rules."""
    if goal == "Retirement Planning":
        return {
            "advice_text": "For retirement, focus on long-term wealth compounding with Equity for growth, Debt for stability, and Gold as a hedge.",
            "allocation": {"Equity": int(0.6 * 100000), "Debt": int(0.3 * 100000), "Gold": int(0.1 * 100000)}
        }
    elif goal == "Short-term Savings":
        return {
             "advice_text": "For short-term goals, prioritize capital protection with Debt instruments. Equity exposure is minimal.",
             "allocation": {"Equity": int(0.1 * 100000), "Debt": int(0.8 * 100000), "Gold": int(0.1 * 100000)}
        }
    elif age < 35 and goal == "Wealth Accumulation":
         return {
             "advice_text": "For wealth creation at a young age, aggressive equity allocation (Mid/Small-cap) is recommended.",
             "allocation": {"Equity": int(0.75 * 100000), "Debt": int(0.2 * 100000), "Gold": int(0.05 * 100000)}
        }
    return None

def generate_ai_recommendation(age, income, profession, region, goal, api_key):
    """Generates investment recommendation using Gemini AI."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            f"As an expert Indian financial advisor, provide a detailed investment recommendation for:\n"
            f"Age: {age}, Income: ₹{income}, Profession: {profession}, Region: {region}, Goal: {goal}\n"
            f"Provide:\n"
            f"1. A concise advice summary (2 small paragraphs).\n"
            f"2. JSON 'allocation' with keys 'Equity', 'Debt', 'Gold' and numeric values.\n"
            f"Format:\n[ADVICE_START]...[ADVICE_END]\n[JSON_START]...[JSON_END]"
        )
        
        response = model.generate_content(prompt)
        text = response.text
        
        advice_match = re.search(r"\[ADVICE_START\](.*?)\[ADVICE_END\]", text, re.DOTALL)
        advice = advice_match.group(1).strip() if advice_match else text
        
        json_match = re.search(r"\[JSON_START\](.*?)\[JSON_END\]", text, re.DOTALL)
        allocation = {"Equity": 0, "Debt": 0, "Gold": 0}
        
        if json_match:
            try:
                data = json.loads(json_match.group(1).strip())
                allocation = data.get("allocation", allocation)
            except: pass
            
        return {"advice_text": advice.replace("*", ""), "allocation": allocation}
    except Exception as e:
        return {"advice_text": f"Error: {str(e)}", "allocation": {"Equity": 0, "Debt": 0, "Gold": 0}}

def search_funds(query):
    """Searches for mutual funds using mfapi.in"""
    url = f"https://api.mfapi.in/mf/search?q={query}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_fund_history(scheme_code):
    """Fetches historical NAV data for a mutual fund."""
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Extract NAV history
            nav_data = data.get("data", [])
            # Return list of {date, nav}
            return [{"date": d["date"], "nav": float(d["nav"])} for d in nav_data[:30]] # Last 30 entries for speed/chart
    except Exception as e:
        print(f"Error fetching fund history: {e}")
        return []
    return []

