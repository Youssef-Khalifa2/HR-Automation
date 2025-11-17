#!/usr/bin/env python3
"""Initialize team mappings in database from CSV file"""
import sys
from app.database import SessionLocal
from app.models.config import TeamMapping
# Import all models to ensure they're registered with SQLAlchemy before any queries
from app.models import user, submission, asset, exit_interview, config
from app.services.leader_mapping import get_leader_mapping

def initialize_mappings_from_csv():
    """Import team mappings from CSV file into database"""
    db = SessionLocal()

    try:
        # Load mappings from CSV
        print("Loading mappings from CSV...")
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
                # Update existing
                existing.team_leader_email = data['leader_email']
                existing.chinese_head_name = data.get('chm_name')
                existing.chinese_head_email = data.get('chm_email')
                existing.department = data.get('department')
                existing.crm = crm
                existing.vendor_email = data.get('vendor_email')
                existing.updated_by = "system_init"
                updated_count += 1
                print(f"Updated: {data['leader_name']}")
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
                    updated_by="system_init"
                )
                db.add(new_mapping)
                imported_count += 1
                print(f"Created: {data['leader_name']}")

        db.commit()

        print("\n" + "="*60)
        print("[SUCCESS] CSV Import Complete!")
        print(f"   New mappings imported: {imported_count}")
        print(f"   Existing mappings updated: {updated_count}")
        print(f"   Total mappings in database: {imported_count + updated_count}")
        print("="*60)

        return True

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Error importing CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = initialize_mappings_from_csv()
    sys.exit(0 if success else 1)
