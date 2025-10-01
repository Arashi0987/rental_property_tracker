from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import requests
import os
from typing import List, Optional
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect('properties.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT,
            price REAL,
            bedrooms INTEGER,
            bathrooms REAL,
            sqft INTEGER,
            property_type TEXT,
            listing_id TEXT UNIQUE,
            estimated_rent REAL,
            monthly_payment REAL,
            monthly_taxes REAL,
            monthly_insurance REAL,
            total_monthly_cost REAL,
            monthly_cash_flow REAL,
            annual_return REAL,
            investment_rating TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Pydantic models
class PropertySearch(BaseModel):
    location: str
    mortgage_rate: float
    desired_return: float
    maintenance_rate: float = 0.015  # 1.5% annually
    management_fee: float = 0.08     # 8% of rental income
    vacancy_rate: float = 0.06       # 6% vacancy

class PropertyResult(BaseModel):
    address: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    property_type: str
    estimated_rent: float
    monthly_payment: float
    monthly_taxes: float
    monthly_insurance: float
    total_monthly_cost: float
    monthly_cash_flow: float
    annual_return: float
    investment_rating: str

# Helper functions
def get_mortgage_payment(principal: float, rate: float, years: int = 30) -> float:
    """Calculate monthly mortgage payment"""
    monthly_rate = rate / 12
    num_payments = years * 12
    if monthly_rate == 0:
        return principal / num_payments
    return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

def get_default_mortgage_rate() -> float:
    """Get current mortgage rate from FRED API"""
    try:
        # Using FRED API for 30-year fixed mortgage rate
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': 'MORTGAGE30US',
            'api_key': 'your_fred_api_key',  # You'll need to get this
            'file_type': 'json',
            'limit': 1,
            'sort_order': 'desc'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return float(data['observations'][0]['value']) / 100
    except:
        pass
    
    # Fallback to a reasonable default
    return 0.07  # 7%

def search_properties(location: str, api_key: str) -> List[dict]:
    """Search for properties using RealtyMole API (RapidAPI)"""
    try:
        url = "https://realty-mole-property-api.p.rapidapi.com/properties"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "realty-mole-property-api.p.rapidapi.com"
        }
        params = {
            "address": location,
            "limit": 20
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error searching properties: {e}")
        return []

def get_rental_estimate(address: str, api_key: str) -> float:
    """Get rental estimate for a property"""
    try:
        url = "https://realty-mole-property-api.p.rapidapi.com/rentalPrice"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "realty-mole-property-api.p.rapidapi.com"
        }
        params = {"address": address}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('rent', 0)
        return 0
    except Exception as e:
        print(f"Error getting rental estimate: {e}")
        return 0

def calculate_investment_metrics(property_data: dict, search_params: PropertySearch) -> dict:
    """Calculate investment metrics for a property"""
    price = property_data.get('price', 0)
    if price == 0:
        return None
    
    # Calculate monthly mortgage payment (assuming 20% down)
    down_payment = price * 0.2
    loan_amount = price - down_payment
    monthly_payment = get_mortgage_payment(loan_amount, search_params.mortgage_rate)
    
    # Estimate monthly taxes and insurance
    monthly_taxes = (price * 0.012) / 12  # 1.2% annually
    monthly_insurance = (price * 0.003) / 12  # 0.3% annually
    
    # Calculate monthly maintenance
    monthly_maintenance = (price * search_params.maintenance_rate) / 12
    
    # Get rental estimate
    estimated_rent = property_data.get('estimated_rent', 0)
    
    # Apply vacancy rate and management fees
    effective_rent = estimated_rent * (1 - search_params.vacancy_rate) * (1 - search_params.management_fee)
    
    # Total monthly costs
    total_monthly_cost = monthly_payment + monthly_taxes + monthly_insurance + monthly_maintenance
    
    # Monthly cash flow
    monthly_cash_flow = effective_rent - total_monthly_cost
    
    # Annual return calculation
    annual_cash_flow = monthly_cash_flow * 12
    total_investment = down_payment  # Initial investment
    annual_return = (annual_cash_flow / total_investment) * 100 if total_investment > 0 else 0
    
    # Investment rating
    if monthly_cash_flow < 0:
        rating = "Not Profitable"
    elif abs(monthly_cash_flow) < 50:  # Break even threshold
        rating = "Break Even"
    elif annual_return < search_params.desired_return:
        rating = "Cash Flowing"
    else:
        rating = "Profitable"
    
    return {
        'estimated_rent': estimated_rent,
        'monthly_payment': monthly_payment,
        'monthly_taxes': monthly_taxes,
        'monthly_insurance': monthly_insurance,
        'total_monthly_cost': total_monthly_cost,
        'monthly_cash_flow': monthly_cash_flow,
        'annual_return': annual_return,
        'investment_rating': rating
    }

# API endpoints
@app.get("/")
async def root():
    return {"message": "Real Estate Investment Analyzer API"}

@app.get("/mortgage-rate")
async def get_current_mortgage_rate():
    """Get current mortgage rate"""
    rate = get_default_mortgage_rate()
    return {"rate": rate}

@app.post("/analyze-properties")
async def analyze_properties(search: PropertySearch):
    """Analyze properties for investment potential"""
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="RapidAPI key not configured")
    
    # Search for properties
    properties = search_properties(search.location, api_key)
    
    if not properties:
        # Return mock data for testing
        properties = [
            {
                "address": "123 Main St, " + search.location,
                "price": 250000,
                "bedrooms": 3,
                "bathrooms": 2.0,
                "sqft": 1500,
                "propertyType": "Single Family",
                "listingId": "mock1"
            },
            {
                "address": "456 Oak Ave, " + search.location,
                "price": 180000,
                "bedrooms": 2,
                "bathrooms": 1.5,
                "sqft": 1200,
                "propertyType": "Townhouse",
                "listingId": "mock2"
            }
        ]
    
    results = []
    conn = sqlite3.connect('properties.db')
    cursor = conn.cursor()
    
    for prop in properties[:10]:  # Limit to 10 properties
        # Get rental estimate
        estimated_rent = get_rental_estimate(prop.get('address', ''), api_key)
        if estimated_rent == 0:
            # Mock rental estimate based on property size and location
            estimated_rent = max(1000, prop.get('sqft', 1000) * 1.2)
        
        prop['estimated_rent'] = estimated_rent
        
        # Calculate investment metrics
        metrics = calculate_investment_metrics(prop, search)
        if metrics:
            result = PropertyResult(
                address=prop.get('address', ''),
                price=prop.get('price', 0),
                bedrooms=prop.get('bedrooms', 0),
                bathrooms=prop.get('bathrooms', 0),
                sqft=prop.get('sqft', 0),
                property_type=prop.get('propertyType', ''),
                **metrics
            )
            results.append(result)
            
            # Save to database
            cursor.execute('''
                INSERT OR REPLACE INTO properties 
                (address, price, bedrooms, bathrooms, sqft, property_type, listing_id,
                 estimated_rent, monthly_payment, monthly_taxes, monthly_insurance,
                 total_monthly_cost, monthly_cash_flow, annual_return, investment_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.address, result.price, result.bedrooms, result.bathrooms,
                result.sqft, result.property_type, prop.get('listingId', ''),
                result.estimated_rent, result.monthly_payment, result.monthly_taxes,
                result.monthly_insurance, result.total_monthly_cost, result.monthly_cash_flow,
                result.annual_return, result.investment_rating
            ))
    
    conn.commit()
    conn.close()
    
    # Sort by investment rating and annual return
    rating_order = {"Profitable": 4, "Cash Flowing": 3, "Break Even": 2, "Not Profitable": 1}
    results.sort(key=lambda x: (rating_order.get(x.investment_rating, 0), x.annual_return), reverse=True)
    
    return {"properties": results}

@app.get("/properties")
async def get_saved_properties():
    """Get all saved properties from database"""
    conn = sqlite3.connect('properties.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM properties ORDER BY annual_return DESC')
    properties = cursor.fetchall()
    conn.close()
    
    return {"properties": properties}

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
