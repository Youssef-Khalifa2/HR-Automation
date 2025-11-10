"""
Leader mapping API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.services.leader_mapping import get_leader_mapping

router = APIRouter(prefix="/api/mapping", tags=["leader-mapping"])


class LeaderSearchRequest(BaseModel):
    query: str


class LeaderInfoResponse(BaseModel):
    leader_name: str
    leader_email: str
    chm_name: Optional[str] = None
    chm_email: Optional[str] = None


@router.get("/leaders", response_model=Dict[str, str])
def get_all_leaders():
    """Get all leader mappings"""
    try:
        mapping = get_leader_mapping()
        leaders = mapping.get_all_leaders()
        return {
            "count": len(leaders),
            "leaders": leaders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaders: {str(e)}")


@router.post("/leaders/search", response_model=Dict[str, str])
def search_leaders(request: LeaderSearchRequest):
    """Search leaders by name"""
    try:
        mapping = get_leader_mapping()
        matches = mapping.search_leaders(request.query)
        return {
            "query": request.query,
            "count": len(matches),
            "matches": matches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search leaders: {str(e)}")


@router.get("/leader/{leader_name}", response_model=LeaderInfoResponse)
def get_leader_info(leader_name: str):
    """Get leader info including CHM details"""
    try:
        mapping = get_leader_mapping()
        info = mapping.get_leader_info(leader_name)

        if not info:
            raise HTTPException(status_code=404, detail=f"Leader '{leader_name}' not found")

        return LeaderInfoResponse(**info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leader info: {str(e)}")


@router.get("/leader/{leader_name}/email")
def get_leader_email(leader_name: str):
    """Get leader email by name"""
    try:
        mapping = get_leader_mapping()
        email = mapping.get_leader_email(leader_name)

        if not email:
            raise HTTPException(status_code=404, detail=f"Leader '{leader_name}' not found")

        return {
            "leader_name": leader_name,
            "leader_email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leader email: {str(e)}")


@router.get("/chm/{chm_name}/email")
def get_chm_email(chm_name: str):
    """Get CHM email by name"""
    try:
        mapping = get_leader_mapping()
        email = mapping.get_chm_email(chm_name)

        if not email:
            raise HTTPException(status_code=404, detail=f"CHM '{chm_name}' not found")

        return {
            "chm_name": chm_name,
            "chm_email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CHM email: {str(e)}")


@router.get("/crm/{crm}")
def get_info_by_crm(crm: str):
    """Get leader and CHM info by CRM identifier"""
    try:
        mapping = get_leader_mapping()
        info = mapping.get_info_by_crm(crm)

        if not info:
            raise HTTPException(status_code=404, detail=f"CRM '{crm}' not found")

        return LeaderInfoResponse(**info)

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
def mapping_health():
    """Check mapping service health"""
    try:
        mapping = get_leader_mapping()
        leaders = mapping.get_all_leaders()
        chms = mapping.chm_mapping

        return {
            "status": "healthy",
            "csv_file": str(mapping.csv_file_path),
            "csv_exists": mapping.csv_file_path.exists(),
            "leaders_count": len(leaders),
            "chms_count": len(chms),
            "sample_leaders": dict(list(leaders.items())[:5])
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }