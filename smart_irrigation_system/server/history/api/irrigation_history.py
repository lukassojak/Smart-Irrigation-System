"""History API router for uploading irrigation records from nodes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlmodel import Session

from smart_irrigation_system.server.history.services.history_service import IrrigationHistoryService
from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.history.schemas.irrigation_history import (
    IrrigationHistoryUploadRequest,
    IrrigationHistoryUploadResponse,
    IrrigationHistoryReadResponse,
)

router = APIRouter()


@router.post(
    "/upload",
    summary="Upload irrigation history from a node",
    response_model=IrrigationHistoryUploadResponse,
    status_code=200
)
def upload_history(
    request: IrrigationHistoryUploadRequest,
    session: Session = Depends(get_session)
) -> IrrigationHistoryUploadResponse:
    """
    Upload irrigation history records from a node.
    
    The node sends all records it has (from potentially multiple days if it was offline).
    The server will:
    1. Check for duplicate records (using node_id + circuit_id + start_time)
    2. Insert only new records
    3. Return how many records were inserted
    
    This ensures robustness against connection failures and offline periods.
    """
    try:
        node_id = request.node_id
        records = request.records

        service = IrrigationHistoryService(session)

        if not records:
            return IrrigationHistoryUploadResponse(uploaded_count=0, message="No records to upload")

        uploaded_count, skipped_count = service.upload_records(node_id=node_id, records=records)

        message = f"Uploaded {uploaded_count} records"
        if skipped_count > 0:
            message += f" (skipped {skipped_count} duplicates)"

        return IrrigationHistoryUploadResponse(uploaded_count=uploaded_count, message=message)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload history: {str(e)}"
        )


@router.get(
    "/records",
    summary="Get irrigation history records",
    status_code=200
)
def get_records(
    node_id: Optional[int] = None,
    circuit_id: Optional[int] = None,
    limit: int = 100,
    include_deleted_zones: bool = False,
    outcome: Optional[str] = None,
    session: Session = Depends(get_session),
) -> IrrigationHistoryReadResponse:
    """
    Retrieve irrigation history records.
    
    Filters:
    - node_id: Get records from specific node
    - circuit_id: Get records from specific circuit
    - limit: Maximum number of records to return (default: 100)
    - include_deleted_zones: Whether to include deleted zones (default: False)
    - outcome: Filter by outcome (if omitted, all outcomes included)
    """
    try:
        service = IrrigationHistoryService(session)
        return service.get_records(
            node_id=node_id,
            circuit_id=circuit_id,
            limit=limit,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.delete(
    "/records",
    summary="Delete irrigation history records",
    status_code=200
)
def delete_records(
    node_id: Optional[int] = None,
    circuit_id: Optional[int] = None,
    session: Session = Depends(get_session)
) -> dict:
    """
    Delete irrigation history records. If `node_id` or `circuit_id` are provided,
    only matching records will be deleted. Otherwise all history records are removed.
    """
    try:
        service = IrrigationHistoryService(session)
        deleted = service.delete_records(node_id=node_id, circuit_id=circuit_id)
        return {"deleted": deleted}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete history: {str(e)}"
        )
