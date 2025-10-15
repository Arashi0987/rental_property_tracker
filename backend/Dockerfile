# Use a lightweight Python image
FROM python:3.11-slim

# Set working dir
WORKDIR /app

# Copy requirements first (for better cache)
COPY backend/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY backend/ ./

# Expose the port your FastAPI app listens on
EXPOSE 8000

# Use uvicorn to run the app; adjust as necessary
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
