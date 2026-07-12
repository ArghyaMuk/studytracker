import httpx

from app.core.config import settings


class CurriculumClient:
    """Typed client for Curriculum Service."""

    def __init__(self):
        self.base_url = settings.curriculum_service_url

    async def get_unit_topics(self, subject_code: str) -> list[dict]:
        """Fetch units and topics for a subject."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/subjects/{subject_code}/units",
                timeout=5.0,
            )
            if response.status_code == 200:
                return response.json()
            return []

    async def get_subject_info(self, subject_code: str) -> dict | None:
        """Fetch subject details including name, type, and units."""
        async with httpx.AsyncClient() as client:
            # Get all programs to find the subject
            # The curriculum service exposes subjects via their code + units
            units_response = await client.get(
                f"{self.base_url}/api/v1/subjects/{subject_code}/units",
                timeout=5.0,
            )
            units = units_response.json() if units_response.status_code == 200 else []

            return {
                "code": subject_code,
                "units": units,
            }

    async def get_subject_with_name(self, subject_code: str, program_id: int | None = None) -> dict:
        """Fetch subject name and unit details for quiz generation context."""
        async with httpx.AsyncClient() as client:
            # Get units for the subject
            units_response = await client.get(
                f"{self.base_url}/api/v1/subjects/{subject_code}/units",
                timeout=5.0,
            )
            units = units_response.json() if units_response.status_code == 200 else []

            # Try to get subject name from programs listing
            # Search through all programs and semesters to find this subject
            subject_name = subject_code  # fallback to code
            try:
                programs_response = await client.get(
                    f"{self.base_url}/api/v1/programs",
                    timeout=5.0,
                )
                if programs_response.status_code == 200:
                    programs = programs_response.json()
                    for prog in programs:
                        for sem in range(1, prog.get("total_semesters", 8) + 1):
                            subjects_response = await client.get(
                                f"{self.base_url}/api/v1/programs/{prog['id']}/semesters/{sem}/subjects",
                                timeout=5.0,
                            )
                            if subjects_response.status_code == 200:
                                for subj in subjects_response.json():
                                    if subj.get("code") == subject_code:
                                        subject_name = subj.get("name", subject_code)
                                        return {
                                            "code": subject_code,
                                            "name": subject_name,
                                            "units": units,
                                        }
            except Exception:
                pass

            return {
                "code": subject_code,
                "name": subject_name,
                "units": units,
            }
