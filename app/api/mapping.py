"""
Leader mapping API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.leader_mapping import get_leader_mapping
from app.database import get_db
from app.models.config import TeamMapping

router = APIRouter(prefix="/api/mapping", tags=["leader-mapping"])


class LeaderSearchRequest(BaseModel):
    query: str


class LeaderInfoResponse(BaseModel):
    leader_name: str
    leader_email: str
    chm_name: Optional[str] = None
    chm_email: Optional[str] = None


class LeadersResponse(BaseModel):
    count: int
    leaders: Dict[str, str]


class CHMsResponse(BaseModel):
    count: int
    chms: Dict[str, str]


class SearchResponse(BaseModel):
    query: str
    count: int
    matches: Dict[str, str]


@router.get("/leaders", response_model=LeadersResponse)
def get_all_leaders(db: Session = Depends(get_db)):
    """Get all leader mappings from database"""
    try:
        # Query active team mappings from database
        mappings = db.query(TeamMapping).filter(TeamMapping.is_active == True).all()

        # Create dictionary of leader names to emails
        leaders = {
            mapping.team_leader_name: mapping.team_leader_email
            for mapping in mappings
            if mapping.team_leader_name and mapping.team_leader_email
        }

        return {
            "count": len(leaders),
            "leaders": leaders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaders: {str(e)}")


@router.get("/chms", response_model=CHMsResponse)
def get_all_chms(db: Session = Depends(get_db)):
    """Get all CHM (Chinese Head) mappings from database"""
    try:
        # Query active team mappings from database
        mappings = db.query(TeamMapping).filter(TeamMapping.is_active == True).all()

        # Create dictionary of CHM names to emails
        chms = {
            mapping.chinese_head_name: mapping.chinese_head_email
            for mapping in mappings
            if mapping.chinese_head_name and mapping.chinese_head_email
        }

        return {
            "count": len(chms),
            "chms": chms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CHMs: {str(e)}")


@router.post("/leaders/search", response_model=SearchResponse)
def search_leaders(request: LeaderSearchRequest, db: Session = Depends(get_db)):
    """Search leaders by name from database"""
    try:
        # Search in database for matching leader names
        mappings = db.query(TeamMapping).filter(
            TeamMapping.is_active == True,
            TeamMapping.team_leader_name.ilike(f"%{request.query}%")
        ).all()

        matches = {
            mapping.team_leader_name: mapping.team_leader_email
            for mapping in mappings
            if mapping.team_leader_name and mapping.team_leader_email
        }

        return {
            "query": request.query,
            "count": len(matches),
            "matches": matches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search leaders: {str(e)}")


@router.get("/leader/{leader_name}", response_model=LeaderInfoResponse)
def get_leader_info(leader_name: str, db: Session = Depends(get_db)):
    """Get leader info including CHM details from database"""
    try:
        # Query database for leader mapping
        mapping = db.query(TeamMapping).filter(
            TeamMapping.is_active == True,
            TeamMapping.team_leader_name == leader_name
        ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail=f"Leader '{leader_name}' not found")

        return LeaderInfoResponse(
            leader_name=mapping.team_leader_name,
            leader_email=mapping.team_leader_email,
            chm_name=mapping.chinese_head_name,
            chm_email=mapping.chinese_head_email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leader info: {str(e)}")


@router.get("/leader/{leader_name}/email")
def get_leader_email(leader_name: str, db: Session = Depends(get_db)):
    """Get leader email by name from database"""
    try:
        mapping = db.query(TeamMapping).filter(
            TeamMapping.is_active == True,
            TeamMapping.team_leader_name == leader_name
        ).first()

        if not mapping or not mapping.team_leader_email:
            raise HTTPException(status_code=404, detail=f"Leader '{leader_name}' not found")

        return {
            "leader_name": leader_name,
            "leader_email": mapping.team_leader_email
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leader email: {str(e)}")


@router.get("/chm/{chm_name}/email")
def get_chm_email(chm_name: str, db: Session = Depends(get_db)):
    """Get CHM email by name from database"""
    try:
        mapping = db.query(TeamMapping).filter(
            TeamMapping.is_active == True,
            TeamMapping.chinese_head_name == chm_name
        ).first()

        if not mapping or not mapping.chinese_head_email:
            raise HTTPException(status_code=404, detail=f"CHM '{chm_name}' not found")

        return {
            "chm_name": chm_name,
            "chm_email": mapping.chinese_head_email
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CHM email: {str(e)}")


@router.get("/crm/{crm}")
def get_info_by_crm(crm: str, db: Session = Depends(get_db)):
    """Get leader and CHM info by CRM identifier from database"""
    try:
        mapping = db.query(TeamMapping).filter(
            TeamMapping.is_active == True,
            TeamMapping.crm == crm
        ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail=f"CRM '{crm}' not found")

        return LeaderInfoResponse(
            leader_name=mapping.team_leader_name,
            leader_email=mapping.team_leader_email,
            chm_name=mapping.chinese_head_name,
            chm_email=mapping.chinese_head_email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CRM info: {str(e)}")


@router.post("/reload")
def reload_mapping():
    """Reload mapping from CSV file"""
    try:
        mapping = get_leader_mapping()
        success = mapping.reload_mapping()

        if success:
            leaders = mapping.get_all_leaders()
            return {
                "message": "Mapping reloaded successfully",
                "leaders_count": len(leaders),
                "timestamp": mapping.csv_file_path.stat().st_mtime
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload mapping")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload mapping: {str(e)}")


@router.get("/health")
def mapping_health(db: Session = Depends(get_db)):
    """Check mapping service health from database"""
    try:
        # Query database for active mappings
        mappings = db.query(TeamMapping).filter(TeamMapping.is_active == True).all()

        leaders = {
            m.team_leader_name: m.team_leader_email
            for m in mappings
            if m.team_leader_name and m.team_leader_email
        }

        chms = {
            m.chinese_head_name: m.chinese_head_email
            for m in mappings
            if m.chinese_head_name and m.chinese_head_email
        }

        return {
            "status": "healthy",
            "source": "database",
            "total_mappings": len(mappings),
            "leaders_count": len(leaders),
            "chms_count": len(chms),
            "sample_leaders": dict(list(leaders.items())[:5])
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }