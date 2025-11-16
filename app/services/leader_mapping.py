"""
Leader mapping service to automatically route emails based on leader names
"""
import csv
import os
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class LeaderMapping:
    """Service to map leader names to emails and handle routing"""

    def __init__(self, csv_file_path: str = None):
        """Initialize the mapping service

        Args:
            csv_file_path: Path to the CSV mapping file. If None, uses default path.
        """
        if csv_file_path is None:
            # Default path to Assets folder
            current_dir = Path(__file__).parent.parent.parent
            csv_file_path = current_dir / "Assets" / "Team Mapping & Contacts.csv"

        self.csv_file_path = Path(csv_file_path)
        self.leader_mapping = {}
        self.chm_mapping = {}
        self.crm_mapping = {}
        self.vendor_mapping = {}  # Map department to vendor email
        self.load_mapping()

    def load_mapping(self):
        """Load mapping data from CSV file"""
        try:
            if not self.csv_file_path.exists():
                logger.error(f"Mapping CSV file not found: {self.csv_file_path}")
                return False

            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    # Skip empty rows - handle None values safely
                    team_leader_name_value = row.get('Team Leader Name') or row.get('Team Leader Name ')
                    if not (team_leader_name_value or '').strip():
                        continue

                    # Map leader name to email
                    leader_name = (row.get('Team Leader Name') or row.get('Team Leader Name ') or '').strip()
                    leader_email = (row.get('Team Leader Email') or row.get('Team Leader Email ') or '').strip()
                    if leader_name and leader_email:
                        self.leader_mapping[leader_name.lower()] = leader_email

                    # Map Chinese head name to email
                    chm_name = (row.get('Chinese Head Name') or row.get('Chinese Head Name ') or '').strip()
                    chm_email = (row.get('Chinese Head Email') or row.get('Chinese Head Email ') or '').strip()
                    if chm_name and chm_email:
                        self.chm_mapping[chm_name.lower()] = chm_email

                    # Map CRM to leader info (handle potential column name variations and spaces)
                    crm = (row.get('Crm') or row.get('Crm ') or row.get('crm') or '').strip()
                    vendor_email = (row.get('Vendor Email') or row.get('Vendor Email ') or '').strip()
                    department = (row.get('Department') or row.get('Department ') or '').strip()

                    if crm and leader_name:
                        self.crm_mapping[crm.lower()] = {
                            'leader_name': leader_name,
                            'leader_email': leader_email,
                            'chm_name': chm_name,
                            'chm_email': chm_email,
                            'vendor_email': vendor_email,
                            'department': department
                        }

                    # Map department to vendor email (if available)
                    if department and vendor_email:
                        self.vendor_mapping[department.lower()] = vendor_email

            logger.info(f"[OK] Loaded mapping from CSV: {len(self.leader_mapping)} leaders, {len(self.chm_mapping)} CHMs, {len(self.crm_mapping)} CRMs, {len(self.vendor_mapping)} vendors")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to load mapping CSV: {str(e)}")
            return False

    def get_leader_email(self, leader_name: str) -> Optional[str]:
        """Get leader email by name

        Args:
            leader_name: Name of the team leader

        Returns:
            Leader email if found, None otherwise
        """
        if not leader_name:
            return None

        email = self.leader_mapping.get(leader_name.lower().strip())
        if email:
            logger.info(f"[OK] Found leader email: {leader_name} -> {email}")
        else:
            logger.warning(f"[WARN] Leader not found in mapping: {leader_name}")

        return email

    def get_chm_email(self, chm_name: str) -> Optional[str]:
        """Get Chinese Head email by name

        Args:
            chm_name: Name of the Chinese Head

        Returns:
            CHM email if found, None otherwise
        """
        if not chm_name:
            return None

        email = self.chm_mapping.get(chm_name.lower().strip())
        if email:
            logger.info(f"[OK] Found CHM email: {chm_name} -> {email}")
        else:
            logger.warning(f"[WARN] CHM not found in mapping: {chm_name}")

        return email

    def get_name_from_email(self, email: str, role: str = 'leader') -> Optional[str]:
        """Get name from email (reverse lookup)

        Args:
            email: Email address to lookup
            role: Role type - 'leader' or 'chm'

        Returns:
            Name if found, None otherwise
        """
        if not email:
            return None

        email_lower = email.lower().strip()

        # Select correct mapping based on role
        mapping = self.chm_mapping if role == 'chm' else self.leader_mapping

        # Reverse lookup: find key (name) by value (email)
        for name, mapped_email in mapping.items():
            if mapped_email.lower() == email_lower:
                return name.title()  # Return proper case name

        return None

    def get_leader_info(self, leader_name: str) -> Optional[Dict[str, str]]:
        """Get complete leader info including CHM details

        Args:
            leader_name: Name of the team leader

        Returns:
            Dict with leader and CHM info if found, None otherwise
        """
        if not leader_name:
            return None

        leader_email = self.get_leader_email(leader_name)
        if not leader_email:
            return None

        # Find CHM info from CRM mapping
        chm_name = None
        chm_email = None

        for crm_data in self.crm_mapping.values():
            if crm_data['leader_name'].lower() == leader_name.lower():
                chm_name = crm_data['chm_name']
                chm_email = crm_data['chm_email']
                break

        return {
            'leader_name': leader_name,
            'leader_email': leader_email,
            'chm_name': chm_name or "Chinese Head",
            'chm_email': chm_email
        }

    def get_info_by_crm(self, crm: str) -> Optional[Dict[str, str]]:
        """Get leader and CHM info by CRM identifier

        Args:
            crm: CRM identifier

        Returns:
            Dict with leader and CHM info if found, None otherwise
        """
        if not crm:
            return None

        info = self.crm_mapping.get(crm.lower().strip())
        if info:
            logger.info(f"[OK] Found CRM mapping: {crm} -> {info['leader_name']} ({info['leader_email']})")
        else:
            logger.warning(f"[WARN] CRM not found in mapping: {crm}")

        return info

    def get_vendor_email(self, department: str = None, leader_name: str = None) -> Optional[str]:
        """Get vendor email by department or leader name

        Args:
            department: Department name
            leader_name: Leader name (alternative lookup)

        Returns:
            Vendor email if found, None otherwise
        """
        from config import settings

        # Try department lookup first
        if department:
            vendor_email = self.vendor_mapping.get(department.lower().strip())
            if vendor_email:
                logger.info(f"[OK] Found vendor email for department {department}: {vendor_email}")
                return vendor_email

        # Try finding via leader name through CRM mapping
        if leader_name:
            for crm_data in self.crm_mapping.values():
                if crm_data['leader_name'].lower() == leader_name.lower():
                    vendor_email = crm_data.get('vendor_email', '')
                    if vendor_email:
                        logger.info(f"[OK] Found vendor email via leader {leader_name}: {vendor_email}")
                        return vendor_email

        # Fallback to HR email
        logger.warning(f"[WARN] No vendor email found for department={department}, leader={leader_name}. Using HR email as fallback.")
        return settings.HR_EMAIL

    def reload_mapping(self):
        """Reload mapping from CSV file"""
        logger.info("[INFO] Reloading leader mapping...")
        self.leader_mapping.clear()
        self.chm_mapping.clear()
        self.crm_mapping.clear()
        self.vendor_mapping.clear()
        return self.load_mapping()

    def get_all_leaders(self) -> Dict[str, str]:
        """Get all leader mappings

        Returns:
            Dict mapping leader names to emails
        """
        return self.leader_mapping.copy()

    def search_leaders(self, query: str) -> Dict[str, str]:
        """Search leaders by name (partial match)

        Args:
            query: Search query

        Returns:
            Dict matching leader names to emails
        """
        if not query:
            return {}

        query = query.lower()
        matches = {}

        for name, email in self.leader_mapping.items():
            if query in name:
                matches[name] = email

        return matches


# Global instance for reuse
_leader_mapping_instance = None

def get_leader_mapping() -> LeaderMapping:
    """Get global leader mapping instance"""
    global _leader_mapping_instance
    if _leader_mapping_instance is None:
        _leader_mapping_instance = LeaderMapping()
    return _leader_mapping_instance