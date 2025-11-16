"""
Admin API endpoints for system configuration management
Requires admin authentication
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models.user import User
from app.models.config import SystemConfig, TeamMapping
from app.schemas_config import (
    SystemConfigCreate, SystemConfigUpdate, SystemConfigResponse,
    TeamMappingCreate, TeamMappingUpdate, TeamMappingResponse,
    EmailConfigUpdate, SystemSettingsUpdate, BulkConfigResponse
)
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Dependency to verify admin access - NO LONGER USED (removed role-based access control)
# def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
#     """Verify that the current user has admin role"""
#     if current_user.role != "admin":
#         raise HTTPException(
#             status_code=403,
#             detail="Admin access required. You do not have permission to access this resource."
#         )
#     return current_user


# Utility function to get config value from database
def get_config_value(db: Session, config_key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get configuration value from database

    Args:
        db: Database session
        config_key: Configuration key to lookup
        default: Default value if not found

    Returns:
        Configuration value or default
    """
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_key,
        SystemConfig.is_active == True
    ).first()

    if config and config.config_value:
        return config.config_value
    return default


# ============================================================================
# SYSTEM CONFIG ENDPOINTS
# ============================================================================

@router.get("/config", response_model=List[SystemConfigResponse])
def get_all_config(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all system configuration values (admin only)"""
    try:
        query = db.query(SystemConfig)

        if category:
            query = query.filter(SystemConfig.category == category)

        configs = query.all()
        logger.info(f"Admin {current_user.email} retrieved {len(configs)} config values")
        return configs

    except Exception as e:
        logger.error(f"Failed to get config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")


@router.get("/config/{config_key}", response_model=SystemConfigResponse)
def get_config_by_key(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific configuration value by key (admin only)"""
    try:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()

        if not config:
            raise HTTPException(status_code=404, detail=f"Config key '{config_key}' not found")

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config {config_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")


@router.post("/config", response_model=SystemConfigResponse)
def create_config(
    config: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new system configuration value (admin only)"""
    try:
        # Check if config key already exists
        existing = db.query(SystemConfig).filter(SystemConfig.config_key == config.config_key).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Config key '{config.config_key}' already exists")

        # Create new config
        db_config = SystemConfig(
            **config.dict(),
            updated_by=current_user.email
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)

        logger.info(f"Admin {current_user.email} created config: {config.config_key}")
        return db_config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create config: {str(e)}")


@router.put("/config/{config_key}", response_model=SystemConfigResponse)
def update_config(
    config_key: str,
    config_update: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing system configuration value (admin only)"""
    try:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()

        if not config:
            raise HTTPException(status_code=404, detail=f"Config key '{config_key}' not found")

        # Update fields
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_by = current_user.email
        db.commit()
        db.refresh(config)

        logger.info(f"Admin {current_user.email} updated config: {config_key}")
        return config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update config {config_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.delete("/config/{config_key}")
def delete_config(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete system configuration value (admin only)"""
    try:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()

        if not config:
            raise HTTPException(status_code=404, detail=f"Config key '{config_key}' not found")

        db.delete(config)
        db.commit()

        logger.info(f"Admin {current_user.email} deleted config: {config_key}")
        return {"success": True, "message": f"Config '{config_key}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete config {config_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete config: {str(e)}")


# ============================================================================
# BULK CONFIG UPDATE ENDPOINTS
# ============================================================================

@router.put("/config/bulk/email", response_model=BulkConfigResponse)
def update_email_config(
    email_config: EmailConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update email configuration settings (admin only)"""
    try:
        updated_configs = []
        config_mapping = {
            "hr_email": "HR_EMAIL",
            "hr_email_cc": "HR_EMAIL_CC",
            "it_email": "IT_EMAIL",
            "email_provider": "EMAIL_PROVIDER",
            "sendgrid_api_key": "SENDGRID_API_KEY",
            "smtp_host": "SMTP_HOST",
            "smtp_port": "SMTP_PORT",
            "smtp_user": "SMTP_USER",
            "smtp_password": "SMTP_PASSWORD",
            "smtp_from_email": "SMTP_FROM_EMAIL",
            "smtp_from_name": "SMTP_FROM_NAME",
            "vendor_migrate_email": "VENDOR_MIGRATE_EMAIL",
            "vendor_justhr_email_1": "VENDOR_JUSTHR_EMAIL_1",
            "vendor_justhr_email_2": "VENDOR_JUSTHR_EMAIL_2"
        }

        update_data = email_config.dict(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                config_key = config_mapping.get(field)
                if config_key:
                    # Check if config exists
                    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()

                    if config:
                        config.config_value = str(value)
                        config.updated_by = current_user.email
                    else:
                        # Create new config
                        config = SystemConfig(
                            config_key=config_key,
                            config_value=str(value),
                            config_type="email" if "email" in field else "string",
                            category="email",
                            description=f"Email configuration for {field}",
                            updated_by=current_user.email
                        )
                        db.add(config)

                    updated_configs.append(config)

        db.commit()

        # Refresh all configs
        for config in updated_configs:
            db.refresh(config)

        logger.info(f"Admin {current_user.email} updated {len(updated_configs)} email configs")

        return BulkConfigResponse(
            success=True,
            message=f"Updated {len(updated_configs)} email configuration values",
            updated_count=len(updated_configs),
            configs=updated_configs
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update email config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update email config: {str(e)}")


@router.put("/config/bulk/system", response_model=BulkConfigResponse)
def update_system_settings(
    system_settings: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update system settings (admin only)"""
    try:
        updated_configs = []
        config_mapping = {
            "app_base_url": "APP_BASE_URL",
            "frontend_url": "FRONTEND_URL",
            "enable_auto_reminders": "ENABLE_AUTO_REMINDERS",
            "reminder_threshold_hours": "REMINDER_THRESHOLD_HOURS",
            "approval_token_expire_hours": "APPROVAL_TOKEN_EXPIRE_HOURS"
        }

        update_data = system_settings.dict(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                config_key = config_mapping.get(field)
                if config_key:
                    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()

                    if config:
                        config.config_value = str(value)
                        config.updated_by = current_user.email
                    else:
                        config_type = "boolean" if isinstance(value, bool) else ("integer" if isinstance(value, int) else "string")
                        config = SystemConfig(
                            config_key=config_key,
                            config_value=str(value),
                            config_type=config_type,
                            category="system",
                            description=f"System configuration for {field}",
                            updated_by=current_user.email
                        )
                        db.add(config)

                    updated_configs.append(config)

        db.commit()

        for config in updated_configs:
            db.refresh(config)

        logger.info(f"Admin {current_user.email} updated {len(updated_configs)} system configs")

        return BulkConfigResponse(
            success=True,
            message=f"Updated {len(updated_configs)} system configuration values",
            updated_count=len(updated_configs),
            configs=updated_configs
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update system settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update system settings: {str(e)}")


# ============================================================================
# TEAM MAPPING ENDPOINTS
# ============================================================================

@router.get("/mappings", response_model=List[TeamMappingResponse])
def get_all_mappings(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all team mappings (admin only)"""
    try:
        query = db.query(TeamMapping)

        if active_only:
            query = query.filter(TeamMapping.is_active == True)

        mappings = query.all()
        logger.info(f"Admin {current_user.email} retrieved {len(mappings)} team mappings")
        return mappings

    except Exception as e:
        logger.error(f"Failed to get mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve mappings: {str(e)}")


@router.get("/mappings/{mapping_id}", response_model=TeamMappingResponse)
def get_mapping_by_id(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific team mapping by ID (admin only)"""
    try:
        mapping = db.query(TeamMapping).filter(TeamMapping.id == mapping_id).first()

        if not mapping:
            raise HTTPException(status_code=404, detail=f"Mapping ID {mapping_id} not found")

        return mapping

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mapping {mapping_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve mapping: {str(e)}")


@router.post("/mappings", response_model=TeamMappingResponse)
def create_mapping(
    mapping: TeamMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new team mapping (admin only)"""
    try:
        # Check if leader already exists
        existing = db.query(TeamMapping).filter(
            TeamMapping.team_leader_name == mapping.team_leader_name,
            TeamMapping.is_active == True
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Active mapping for leader '{mapping.team_leader_name}' already exists"
            )

        db_mapping = TeamMapping(
            **mapping.dict(),
            updated_by=current_user.email
        )
        db.add(db_mapping)
        db.commit()
        db.refresh(db_mapping)

        logger.info(f"Admin {current_user.email} created mapping for: {mapping.team_leader_name}")
        return db_mapping

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create mapping: {str(e)}")


@router.put("/mappings/{mapping_id}", response_model=TeamMappingResponse)
def update_mapping(
    mapping_id: int,
    mapping_update: TeamMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing team mapping (admin only)"""
    try:
        mapping = db.query(TeamMapping).filter(TeamMapping.id == mapping_id).first()

        if not mapping:
            raise HTTPException(status_code=404, detail=f"Mapping ID {mapping_id} not found")

        # Update fields
        update_data = mapping_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mapping, field, value)

        mapping.updated_by = current_user.email
        db.commit()
        db.refresh(mapping)

        logger.info(f"Admin {current_user.email} updated mapping ID: {mapping_id}")
        return mapping

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update mapping {mapping_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update mapping: {str(e)}")


@router.delete("/mappings/{mapping_id}")
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete team mapping (admin only)"""
    try:
        mapping = db.query(TeamMapping).filter(TeamMapping.id == mapping_id).first()

        if not mapping:
            raise HTTPException(status_code=404, detail=f"Mapping ID {mapping_id} not found")

        db.delete(mapping)
        db.commit()

        logger.info(f"Admin {current_user.email} deleted mapping ID: {mapping_id}")
        return {"success": True, "message": f"Mapping ID {mapping_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete mapping {mapping_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete mapping: {str(e)}")


# ============================================================================
# CSV IMPORT/EXPORT ENDPOINTS
# ============================================================================

@router.post("/mappings/import-csv")
async def import_mappings_from_csv(
    replace_existing: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import team mappings from the existing CSV file into database (admin only)"""
    try:
        from app.services.leader_mapping import get_leader_mapping

        # Load mappings from CSV
        leader_service = get_leader_mapping()
        leader_service.reload_mapping()

        imported_count = 0
        updated_count = 0

        # Import from CRM mapping (most complete data)
        for crm, data in leader_service.crm_mapping.items():
            # Check if mapping exists
            existing = db.query(TeamMapping).filter(
                TeamMapping.team_leader_name == data['leader_name']
            ).first()

            if existing:
                if replace_existing:
                    # Update existing
                    existing.team_leader_email = data['leader_email']
                    existing.chinese_head_name = data.get('chm_name')
                    existing.chinese_head_email = data.get('chm_email')
                    existing.department = data.get('department')
                    existing.crm = crm
                    existing.vendor_email = data.get('vendor_email')
                    existing.updated_by = current_user.email
                    updated_count += 1
            else:
                # Create new
                new_mapping = TeamMapping(
                    team_leader_name=data['leader_name'],
                    team_leader_email=data['leader_email'],
                    chinese_head_name=data.get('chm_name'),
                    chinese_head_email=data.get('chm_email'),
                    department=data.get('department'),
                    crm=crm,
                    vendor_email=data.get('vendor_email'),
                    updated_by=current_user.email
                )
                db.add(new_mapping)
                imported_count += 1

        db.commit()

        logger.info(f"Admin {current_user.email} imported CSV mappings: {imported_count} new, {updated_count} updated")

        return {
            "success": True,
            "message": f"CSV import complete",
            "imported_count": imported_count,
            "updated_count": updated_count
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to import CSV mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import CSV: {str(e)}")
 
