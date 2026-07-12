import httpx

from app.core.config import settings


class CurriculumClient:
    """Typed HTTP client for the Curriculum Service."""

    def __init__(self):
        self.base_url = settings.curriculum_service_url

    async def validate_subject_unit(self, subject_code: str, unit_number: int) -> bool:
        """Check if a subject code and unit number are valid."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/subjects/{subject_code}/units",
                    timeout=5.0,
                )
                if response.status_code != 200:
                    return False
                units = response.json()
                return any(u["unit_number"] == unit_number for u in units)
        except httpx.RequestError:
            raise RuntimeError("Curriculum service unavailable")
