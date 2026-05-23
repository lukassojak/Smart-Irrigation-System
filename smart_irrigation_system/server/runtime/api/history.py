"""History API router for uploading irrigation records from nodes."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select

from smart_irrigation_system.server.configuration.repositories.zone_lifecycle_repository import ZoneLifecycleRepository
from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory

router = APIRouter()


class IrrigationRecordInput(BaseModel):
    """Input model for a single irrigation record from the node."""
    circuit_id: int = Field(..., description="Circuit/zone ID on the node")
    start_time: datetime = Field(..., description="When irrigation started")
    outcome: str = Field(..., description="Outcome: COMPLETED, INTERRUPTED, SKIPPED")
    completed_duration: Optional[int] = Field(None, description="Actual duration in seconds")
    target_duration: Optional[int] = Field(None, description="Target duration in seconds")
    actual_water_amount: Optional[float] = Field(None, description="Actual water used in liters")
    target_water_amount: Optional[float] = Field(None, description="Target water amount in liters")
    reason: Optional[str] = Field(None, description="Reason if interrupted or skipped")


class HistoryUploadRequest(BaseModel):
    """Request model for uploading irrigation history from a node."""
    node_id: int = Field(..., description="Node ID")
    records: List[IrrigationRecordInput] = Field(..., description="List of irrigation records")


class HistoryUploadResponse(BaseModel):
    """Response after uploading history."""
    uploaded_count: int
    message: str


@router.post(
    "/upload",
    summary="Upload irrigation history from a node",
    response_model=HistoryUploadResponse,
    status_code=200
)
def upload_history(
    request: HistoryUploadRequest,
    session: Session = Depends(get_session)
) -> HistoryUploadResponse:
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
        lifecycle_repo = ZoneLifecycleRepository(session)
        
        if not records:
            return HistoryUploadResponse(uploaded_count=0, message="No records to upload")
        
        uploaded_count = 0
        skipped_count = 0
        
        for record_input in records:
            # Check if record already exists (to prevent duplicates)
            existing = session.exec(
                select(IrrigationHistory).where(
                    IrrigationHistory.node_id == node_id,
                    IrrigationHistory.circuit_id == record_input.circuit_id,
                    IrrigationHistory.start_time == record_input.start_time
                )
            ).first()
            
            if existing:
                skipped_count += 1
                continue

            lifecycle = lifecycle_repo.get_applicable(node_id, record_input.circuit_id, record_input.start_time)
            zone_deleted = bool(lifecycle and lifecycle.deleted_at is not None)
            
            # Create and add new record
            history_record = IrrigationHistory(
                node_id=node_id,
                circuit_id=record_input.circuit_id,
                zone_deleted=zone_deleted,
                start_time=record_input.start_time,
                outcome=record_input.outcome,
                completed_duration=record_input.completed_duration,
                target_duration=record_input.target_duration,
                actual_water_amount=record_input.actual_water_amount,
                target_water_amount=record_input.target_water_amount,
                reason=record_input.reason,
            )
            session.add(history_record)
            uploaded_count += 1
        
        # Commit all new records
        session.commit()
        
        message = f"Uploaded {uploaded_count} records"
        if skipped_count > 0:
            message += f" (skipped {skipped_count} duplicates)"
        
        return HistoryUploadResponse(
            uploaded_count=uploaded_count,
            message=message
        )
        
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
    session: Session = Depends(get_session)
) -> dict:
    """
    Retrieve irrigation history records.
    
    Filters:
    - node_id: Get records from specific node
    - circuit_id: Get records from specific circuit
    - limit: Maximum number of records to return (default: 100)
    """
    try:
        query = select(IrrigationHistory)
        
        if node_id is not None:
            query = query.where(IrrigationHistory.node_id == node_id)
        
        if circuit_id is not None:
            query = query.where(IrrigationHistory.circuit_id == circuit_id)
        
        # Order by start_time descending (newest first)
        query = query.order_by(IrrigationHistory.start_time.desc()).limit(limit)
        
        records = session.exec(query).all()
        
        return {
            "records": records,
            "count": len(records)
        }
        
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
        query = select(IrrigationHistory)

        if node_id is not None:
            query = query.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            query = query.where(IrrigationHistory.circuit_id == circuit_id)

        records = session.exec(query).all()
        deleted = 0
        for r in records:
            session.delete(r)
            deleted += 1

        session.commit()

        return {"deleted": deleted}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete history: {str(e)}"
        )
