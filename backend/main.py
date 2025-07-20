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
from services.pay_calculator import PayCalculator

app = FastAPI(
    title="Pay Calculator API",
    description="API for calculating pay based on shifts worked and applicable rules",
    version="1.0.0"
)

print("✅ Received a request from frontend")



# // Local development CORS settings
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["https://pay-calculator-s0bv.onrender.com"],  # Your frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow ANY origin — useful for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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