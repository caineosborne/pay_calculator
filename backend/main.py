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

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from models.request_models import PayRequest
from models.response_models import PayResponse
from models.auth_models import AuthenticatedUser, LoginRequest
from models.rule_configuration_models import (
    CreateRuleConfigurationRequest,
    RenameRuleConfigurationRequest,
    RuleSourceValidationRequest,
    UpdateRuleConfigurationRequest,
)
from services.award_registry import public_awards, public_disclaimers
from services.pay_calculator import PayCalculator
from services.rule_configurations import (
    RuleConfigurationConflict,
    RuleConfigurationError,
    RuleConfigurationNotFound,
    create_custom_rule,
    delete_custom_rule,
    get_rule_configuration,
    list_rule_configurations,
    rename_custom_rule,
    update_custom_rule,
    validate_rule_payload,
)
from services.rule_configuration_store import DatabaseUnavailable
from services.auth_store import (
    AuthenticationNotConfigured,
    SESSION_COOKIE_NAME,
    SESSION_TTL,
    authenticate,
    public_user,
    revoke_session,
    user_for_session,
)
from services.rule_configurations import BUILTIN_ID_PREFIX

app = FastAPI(
    title="Pay Calculator API",
    description="API for calculating pay based on shifts worked and applicable rules",
    version="1.0.0"
)

# Explicit origins keep the trusted local editor available without opening the
# calculation API to arbitrary browser origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        # "https://pay-calculator-s0bv.onrender.com",
        # "https://pay-calculator.onrender.com",
        # "https://pay-checker-mvp.onrender.com",
        # "https://pay-check.onrender.com",
        "https://pay-calculator-gules.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/awards")
def get_awards() -> list[dict]:
    """
    Return the public award registry used by the frontend selector.
    """
    return public_awards()


@app.get("/disclaimers")
def get_disclaimers() -> dict:
    """Return the calculator and award-specific limitations notices."""
    return public_disclaimers()


def _configuration_http_error(error: RuleConfigurationError) -> HTTPException:
    if isinstance(error, RuleConfigurationNotFound):
        status_code = 404
    elif isinstance(error, RuleConfigurationConflict):
        status_code = 409
    else:
        status_code = 422
    return HTTPException(status_code=status_code, detail=str(error))


def _database_http_error(error: DatabaseUnavailable) -> HTTPException:
    return HTTPException(status_code=503, detail=str(error))


def current_user(request: Request) -> dict | None:
    """Resolve an optional opaque session without exposing its token to JavaScript."""
    try:
        return user_for_session(request.cookies.get(SESSION_COOKIE_NAME))
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


def authenticated_user(user: dict | None = Depends(current_user)) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to save custom rules.")
    return user


@app.post("/auth/login", response_model=AuthenticatedUser)
def login(data: LoginRequest, response: Response) -> dict:
    try:
        authenticated = authenticate(data.username, data.password)
    except AuthenticationNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error
    if authenticated is None:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token, user = authenticated
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    return public_user(user)


@app.get("/auth/me", response_model=AuthenticatedUser)
def get_current_user(user: dict = Depends(authenticated_user)) -> dict:
    return public_user(user)


@app.post("/auth/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    try:
        revoke_session(request.cookies.get(SESSION_COOKIE_NAME))
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


@app.get("/rule-configurations")
def get_rule_configurations(
    user: dict | None = Depends(current_user),
) -> list[dict]:
    """List public built-ins and the current user's private configurations."""
    try:
        owner_id = user["id"] if user else None
        return list_rule_configurations(owner_id)
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


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
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


@app.get("/rule-configurations/{configuration_id}")
def get_configuration(
    configuration_id: str,
    user: dict | None = Depends(current_user),
) -> dict:
    """Return one configuration and its Python source."""
    try:
        owner_id = user["id"] if user else None
        return get_rule_configuration(configuration_id, owner_id)
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


@app.post("/rule-configurations", status_code=201)
def create_configuration(
    data: CreateRuleConfigurationRequest,
    user: dict = Depends(authenticated_user),
) -> dict:
    """Save a validated configuration as a database-backed override."""
    try:
        return create_custom_rule(
            data.base_award,
            data.name,
            data.source,
            data.questionnaire,
            user["id"],
        )
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


@app.put("/rule-configurations/{configuration_id}")
def update_configuration(
    configuration_id: str,
    data: UpdateRuleConfigurationRequest,
    user: dict = Depends(authenticated_user),
) -> dict:
    """Replace a database-backed custom override after validation."""
    try:
        return update_custom_rule(
            configuration_id, data.source, data.questionnaire, user["id"]
        )
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


@app.patch("/rule-configurations/{configuration_id}/name")
def rename_configuration(
    configuration_id: str,
    data: RenameRuleConfigurationRequest,
    user: dict = Depends(authenticated_user),
) -> dict:
    """Rename a custom configuration without modifying its saved overrides."""
    try:
        return rename_custom_rule(configuration_id, data.name, user["id"])
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


@app.delete("/rule-configurations/{configuration_id}", status_code=204)
def delete_configuration(
    configuration_id: str,
    user: dict = Depends(authenticated_user),
) -> None:
    """Delete a custom configuration; built-in configurations are immutable."""
    try:
        delete_custom_rule(configuration_id, user["id"])
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error


@app.post("/calculate", response_model=PayResponse)
def calculate_pay(
    data: PayRequest,
    user: dict | None = Depends(current_user),
) -> PayResponse:
    """Calculate pay from the validated request."""
    try:
        uses_custom_configuration = bool(
            data.rule_configuration
            and not data.rule_configuration.startswith(BUILTIN_ID_PREFIX)
        )
        if uses_custom_configuration and user is None:
            raise HTTPException(
                status_code=401,
                detail="Sign in to use a saved custom configuration.",
            )
        calculator = PayCalculator(data, user["id"] if user else None)
        result = calculator.calculate_pay()
    except RuleConfigurationError as error:
        raise _configuration_http_error(error) from error
    except DatabaseUnavailable as error:
        raise _database_http_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return result
