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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.request_models import PayRequest
from models.response_models import PayResponse
from models.rule_configuration_models import (
    CreateRuleConfigurationRequest,
    RuleSourceValidationRequest,
    UpdateRuleConfigurationRequest,
)
from services.award_registry import public_awards
from services.pay_calculator import PayCalculator
from services.rule_configurations import (
    RuleConfigurationConflict,
    RuleConfigurationError,
    RuleConfigurationNotFound,
    create_custom_rule,
    get_rule_configuration,
    list_rule_configurations,
    update_custom_rule,
    validate_rule_payload,
)

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


def _configuration_http_error(error: RuleConfigurationError) -> HTTPException:
    if isinstance(error, RuleConfigurationNotFound):
        status_code = 404
    elif isinstance(error, RuleConfigurationConflict):
        status_code = 409
    else:
        status_code = 422
    return HTTPException(status_code=status_code, detail=str(error))


@app.get("/rule-configurations")
def get_rule_configurations() -> list[dict]:
    """List immutable built-ins and editable custom rule files."""
    return list_rule_configurations()


@app.post("/rule-configurations/validate")
def validate_configuration(data: RuleSourceValidationRequest) -> dict:
    """Validate rule source without saving it."""
    try:
        return validate_rule_payload(
            data.base_award,
            data.source,
            data.questionnaire,
            allow_invalid_questionnaire=True,
        )
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error


@app.get("/rule-configurations/{configuration_id}")
def get_configuration(configuration_id: str) -> dict:
    """Return one configuration and its Python source."""
    try:
        return get_rule_configuration(configuration_id)
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error


@app.post("/rule-configurations", status_code=201)
def create_configuration(data: CreateRuleConfigurationRequest) -> dict:
    """Save validated source as a new custom rule file."""
    try:
        return create_custom_rule(
            data.base_award, data.name, data.source, data.questionnaire
        )
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error


@app.put("/rule-configurations/{configuration_id}")
def update_configuration(
    configuration_id: str, data: UpdateRuleConfigurationRequest
) -> dict:
    """Replace a custom rule file after validation."""
    try:
        return update_custom_rule(
            configuration_id, data.source, data.questionnaire
        )
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error


@app.post("/calculate", response_model=PayResponse)
def calculate_pay(data: PayRequest) -> PayResponse:
    """
    Calculate pay based on provided shifts and hourly rate.
    """
    print("Received request data:", data.dict())  # Debug log
    try:
        calculator = PayCalculator(data)
        result = calculator.calculate_pay()
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error
    print("Calculated response:", result.dict())  # Debug log
    return result
