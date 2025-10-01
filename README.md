# Real Estate Investment Analyzer

A web application that analyzes rental property investments using real estate market data.

## Features

- **Property Search**: Search by location (city, state, or ZIP code)
- **Investment Analysis**: Calculate cash flow, annual returns, and investment ratings
- **Customizable Parameters**: Adjust mortgage rates, maintenance costs, management fees, and vacancy rates
- **Property Ratings**: Categorizes properties as Not Profitable, Break Even, Cash Flowing, or Profitable

## Setup Instructions

### 1. Backend Setup (Python)

```bash
cd backend
source venv/bin/activate
```

### 2. Configure API Keys

Edit `backend/.env` and add your API keys:

```env
# Required: Your RapidAPI key for Realtor.com API
RAPIDAPI_KEY=your_rapidapi_key_here

# Optional: FRED API key for current mortgage rates
FRED_API_KEY=your_fred_api_key_here
```

### 3. Get Your RapidAPI Key

1. Go to [RapidAPI Realtor.com API](https://rapidapi.com/apidojo/api/realtor/)
2. Subscribe to the free plan
3. Copy your X-RapidAPI-Key
4. Paste it in the `.env` file

### 4. Start the Servers

Backend (Python FastAPI):
```bash
cd backend
source venv/bin/activate
python main.py
```

Frontend (Next.js):
```bash
cd frontend
bun run dev
```

## How It Works

1. **Input Parameters**: Enter location and investment criteria
2. **Property Search**: Uses Realtor.com API to find properties for sale
3. **Rental Analysis**: Estimates rental income for each property
4. **Financial Calculations**: 
   - Monthly mortgage payment (assumes 20% down)
   - Property taxes (1.2% annually)
   - Insurance (0.3% annually)
   - Maintenance costs (customizable)
   - Management fees (customizable)
   - Vacancy adjustments (customizable)
5. **Investment Rating**: 
   - **Not Profitable**: Negative cash flow
   - **Break Even**: Cash flow near zero
   - **Cash Flowing**: Positive cash flow but below desired return
   - **Profitable**: Meets desired return threshold

## Technology Stack

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python, FastAPI, SQLite
- **APIs**: Realtor.com (via RapidAPI), FRED (optional)

## Database

The app uses SQLite to store analyzed properties locally. The database is automatically created when you first run the backend.

## Mock Data

If no API key is provided, the app will use mock data for testing purposes.
