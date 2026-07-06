"""
Main FastAPI application entry point.

This module serves as the entry point for the pay calculation API. It:
1. Sets up the FastAPI application and CORS middleware
2. Provides the main /calculate endpoint
3. Delegates calculation logic to the PayCalculator service

Dependencies:
- models.request_models: Contains PayRequest model for input validation
- models.response_models: Contains PayResponse model for response structure
- services.pay_calculator: Contains PayCalculator for business logic
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.request_models import PayRequest
from models.response_models import PayResponse
from services.award_registry import public_awards
from services.pay_calculator import PayCalculator

app = FastAPI(
    title="Pay Calculator API",
    description="API for calculating pay based on shifts worked and applicable rules",
    version="1.0.0"
)

# Configure CORS
# Allow both local development and production origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        # Production domains
        "https://pay-calculator-s0bv.onrender.com",
        "https://pay-calculator.onrender.com",  
        # Add your actual production frontend domain
        "https://pay-checker-mvp.onrender.com",
        "https://pay-check.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow ANY origin — useful for debugging
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/awards")
def get_awards() -> list[dict]:
    """
    Return the public award registry used by the frontend selector.
    """
    return public_awards()


@app.post("/calculate", response_model=PayResponse)
def calculate_pay(data: PayRequest) -> PayResponse:
    """
    Calculate pay based on provided shifts and hourly rate.
    """
    print("Received request data:", data.dict())  # Debug log
    calculator = PayCalculator(data)
    result = calculator.calculate_pay()
    print("Calculated response:", result.dict())  # Debug log
    return result
