"""Asset management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.asset import Asset
from app.models.submission import Submission
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas_all import AssetCreate, AssetUpdate, AssetResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("/submissions/{submission_id}/assets", response_model=AssetResponse)
def create_or_update_asset(
    submission_id: int,
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update asset record for submission"""
    # Check if submission exists
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Check if asset already exists
    existing_asset = db.query(Asset).filter(Asset.res_id == submission_id).first()

    if existing_asset:
        # Update existing asset
        for key, value in asset_data.dict(exclude_unset=True).items():
            setattr(existing_asset, key, value)
        db.commit()
        db.refresh(existing_asset)
        logger.info(f"Updated asset record for submission {submission_id}")
        return existing_asset
    else:
        # Create new asset
        new_asset = Asset(
            res_id=submission_id,
            assets_returned=asset_data.assets_returned,
            notes=asset_data.notes
        )
        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)
        logger.info(f"Created asset record for submission {submission_id}")
        return new_asset


@router.get("/")
def list_assets(
    returned: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List assets with employee information"""
    # Use proper join with both Asset and Submission models
    query = db.query(Asset, Submission).join(Submission, Asset.res_id == Submission.id)

    if returned is not None:
        query = query.filter(Asset.assets_returned == returned)

    results = query.offset(skip).limit(limit).all()

    # Return assets with submission data from the join
    result = []
    for asset, submission in results:
        result.append({
            "id": asset.id,
            "res_id": asset.res_id,
            "assets_returned": asset.assets_returned,
            "notes": asset.notes,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "department": submission.department,
            "resignation_status": submission.resignation_status,
            "last_working_day": submission.last_working_day.strftime("%Y-%m-%d") if submission.last_working_day else "N/A"
        })

    return result


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset by ID"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/{asset_id}/mark-returned")
async def mark_asset_returned(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark assets as returned"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.assets_returned = True
    db.commit()
    db.refresh(asset)

    # Update submission status to assets_recorded
    submission = db.query(Submission).filter(Submission.id == asset.res_id).first()
    if submission and submission.resignation_status == "exit_done":
        submission.resignation_status = "assets_recorded"
        db.commit()

    logger.info(f"Assets marked as returned for submission {asset.res_id}")

    return {
        "message": "Assets marked as returned successfully",
        "asset_id": asset_id,
        "submission_id": asset.res_id
    }


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete asset record"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()

    logger.info(f"Deleted asset {asset_id}")
    return {"message": "Asset deleted successfully"}
