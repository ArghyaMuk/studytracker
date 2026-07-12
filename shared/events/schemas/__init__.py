"""Event payload schemas defined as Python dictionaries (JSON Schema format).

These serve as the shared contract between event producers and consumers.
"""

SESSION_LOGGED_SCHEMA = {
    "title": "session.logged",
    "description": "Published when a study session is logged",
    "type": "object",
    "required": ["user_id", "subject_code", "unit_number", "duration_minutes", "focus_rating", "session_timestamp"],
    "properties": {
        "user_id": {"type": "integer"},
        "subject_code": {"type": "string", "maxLength": 50},
        "unit_number": {"type": "integer", "minimum": 1},
        "duration_minutes": {"type": "integer", "minimum": 1, "maximum": 480},
        "focus_rating": {"type": "integer", "minimum": 1, "maximum": 5},
        "session_timestamp": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}

SESSION_DELETED_SCHEMA = {
    "title": "session.deleted",
    "description": "Published when a study session is soft-deleted",
    "type": "object",
    "required": ["user_id", "subject_code", "unit_number", "session_id"],
    "properties": {
        "user_id": {"type": "integer"},
        "subject_code": {"type": "string", "maxLength": 50},
        "unit_number": {"type": "integer", "minimum": 1},
        "session_id": {"type": "integer"},
    },
    "additionalProperties": False,
}

QUIZ_COMPLETED_SCHEMA = {
    "title": "quiz.completed",
    "description": "Published when a quiz is submitted and graded",
    "type": "object",
    "required": ["user_id", "subject_code", "unit_number", "score_percentage", "question_count", "quiz_type"],
    "properties": {
        "user_id": {"type": "integer"},
        "subject_code": {"type": "string", "maxLength": 50},
        "unit_number": {"type": "integer", "minimum": 1},
        "score_percentage": {"type": "number", "minimum": 0, "maximum": 100},
        "question_count": {"type": "integer", "minimum": 1},
        "quiz_type": {"type": "string", "enum": ["unit", "pyq", "viva", "weak_topic"]},
        "completion_timestamp": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}

READINESS_UPDATED_SCHEMA = {
    "title": "readiness.updated",
    "description": "Published when a readiness score is recomputed",
    "type": "object",
    "required": ["user_id", "subject_code", "previous_score", "new_score", "computation_timestamp"],
    "properties": {
        "user_id": {"type": "integer"},
        "subject_code": {"type": "string", "maxLength": 50},
        "unit_number": {"type": ["integer", "null"]},
        "previous_score": {"type": "number", "minimum": 0, "maximum": 100},
        "new_score": {"type": "number", "minimum": 0, "maximum": 100},
        "computation_timestamp": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}

# Registry mapping event types to schemas
EVENT_SCHEMAS = {
    "session.logged": SESSION_LOGGED_SCHEMA,
    "session.deleted": SESSION_DELETED_SCHEMA,
    "quiz.completed": QUIZ_COMPLETED_SCHEMA,
    "readiness.updated": READINESS_UPDATED_SCHEMA,
}
