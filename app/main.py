"""
FastAPI Main Application for Cold-Chain Produce Spoilage Alert Service.

ISE2501 CA3: Specialized Tool Exploration & Program Unit/API Testing.
Provides RESTful endpoints for produce registration, sensor telemetry ingest,
batch risk status retrieval, and automated spoilage alert notifications.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator

from app.auth import authenticate_user, create_access_token, require_auth
from app.validators import (
    validate_temperature,
    validate_humidity,
    validate_produce_range,
    validate_produce_type,
    validate_batch_id,
    validate_timestamp,
)
from app.store import store

app = FastAPI(
    title="Cold-Chain Produce Spoilage Alert Service",
    description="Automated QA Lab Project (ISE2501 CA3) - Spoilage Risk Engine",
    version="1.0.0",
)


# --- Custom Exception Handlers for Exact Status Code Mapping ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Maps Pydantic validation errors:
    - Missing required fields, type mismatch (e.g. string for float, boolean) -> 400 Bad Request
    - Semantic boundary check failures -> 422 Unprocessable Entity
    """
    errors = exc.errors()
    for err in errors:
        err_type = str(err.get("type", "")).lower()
        err_msg = str(err.get("msg", "")).lower()
        if (
            "missing" in err_type
            or "type" in err_type
            or "json" in err_type
            or "parsing" in err_type
            or "boolean" in err_msg
            or "number" in err_msg
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Bad Request: Malformed JSON or invalid parameter types",
                    "errors": jsonable_encoder(errors),
                },
            )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Unprocessable Entity: Input values violated business validation rules",
            "errors": jsonable_encoder(errors),
        },
    )


# --- Request & Response Models ---

class LoginRequest(BaseModel):
    username: str
    password: str


class ProduceRegisterRequest(BaseModel):
    name: str
    min_temp_c: float
    max_temp_c: float


class ReadingRequest(BaseModel):
    batch_id: str
    produce_type: str
    temperature_c: float
    humidity_pct: float
    timestamp: str

    @field_validator("temperature_c", "humidity_pct", mode="before")
    @classmethod
    def reject_bool(cls, v):
        if isinstance(v, bool):
            raise ValueError("Sensor value cannot be a boolean")
        return v


# --- Endpoints ---

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Cold-Chain Spoilage Alert Service",
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/login", tags=["Auth"])
async def login(credentials: LoginRequest):
    """
    Authenticates operator/manager credentials and returns a signed PyJWT token.
    Preloaded demo users:
    - operator_alice: securepass123
    - manager_bob: coldchain2026
    """
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": credentials.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/produce", status_code=status.HTTP_201_CREATED, tags=["Produce"])
async def register_produce(
    payload: ProduceRegisterRequest,
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Registers a new produce type with safe temperature boundaries.
    Requires valid JWT token.
    """
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produce name cannot be empty",
        )

    try:
        min_c, max_c = validate_produce_range(payload.min_temp_c, payload.max_temp_c)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    saved_min, saved_max = store.register_produce_type(payload.name, min_c, max_c)
    return {
        "name": payload.name.strip().lower(),
        "min_temp_c": saved_min,
        "max_temp_c": saved_max,
        "status": "registered",
    }


@app.post("/readings", tags=["Telemetry"])
async def submit_reading(
    payload: ReadingRequest,
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Submits a sensor reading for a produce batch.
    Validates physical limits, produce catalog existence, and timestamp window.
    Duplicate readings (same batch and timestamp) are safely ignored without altering state.
    """
    # 1. Validate Batch ID
    try:
        batch_id = validate_batch_id(payload.batch_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 2. Validate Produce Type against registered store catalog
    produce_types = store.get_all_produce_types()
    try:
        produce_type = validate_produce_type(payload.produce_type, produce_types)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # 3. Validate Temperature & Humidity ranges
    try:
        temp_val = validate_temperature(payload.temperature_c)
        hum_val = validate_humidity(payload.humidity_pct)
    except TypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # 4. Validate Timestamp constraints
    try:
        ts_val = validate_timestamp(payload.timestamp)
    except TypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # 5. Record reading in in-memory store
    result = store.record_reading(
        batch_id=batch_id,
        produce_type=produce_type,
        temperature_c=temp_val,
        humidity_pct=hum_val,
        timestamp_dt=ts_val,
    )

    if result.get("status") == "ignored":
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=result)


@app.get("/batches/{batch_id}/status", tags=["Batches"])
async def get_batch_status(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Retrieves current spoilage risk score and risk level (OK, WARNING, CRITICAL)
    for a given batch.
    """
    batch = store.get_batch(batch_id.strip())
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch '{batch_id}' not found",
        )
    return batch


@app.get("/alerts", tags=["Alerts"])
async def list_alerts(
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Lists all active and acknowledged spoilage breach alerts.
    """
    alerts = store.list_alerts()
    return {"alerts": alerts, "total": len(alerts)}


@app.post("/alerts/{alert_id}/ack", tags=["Alerts"])
async def acknowledge_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Acknowledges an active alert.
    """
    updated = store.acknowledge_alert(alert_id.strip())
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found",
        )
    return {"status": "acknowledged", "alert": updated}
