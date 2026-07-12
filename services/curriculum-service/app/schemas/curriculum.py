from pydantic import BaseModel, Field


class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    total_semesters: int = Field(..., ge=1, le=12)


class ProgramResponse(BaseModel):
    id: int
    name: str
    total_semesters: int

    class Config:
        from_attributes = True


class SubjectUnitCreate(BaseModel):
    unit_number: int = Field(..., ge=1, le=20)
    unit_title: str = Field(..., min_length=1, max_length=300)
    topics_json: str | None = None  # JSON array of topic keywords


class SubjectUnitResponse(BaseModel):
    id: int
    unit_number: int
    unit_title: str
    topics_json: str | None

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    semester: int = Field(..., ge=1, le=12)
    type: str  # "theory" or "lab"
    credits: int = Field(3, ge=1, le=10)
    units: list[SubjectUnitCreate] = Field(default_factory=list)


class SubjectResponse(BaseModel):
    id: int
    code: str
    name: str
    semester: int
    type: str
    credits: int
    units: list[SubjectUnitResponse] = []

    class Config:
        from_attributes = True
