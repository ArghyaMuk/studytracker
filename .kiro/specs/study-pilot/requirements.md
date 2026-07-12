# Requirements Document

## Introduction

StudyPilot is an AI-powered study and exam readiness platform for college students across any degree program. Built as a Python microservices application around a semester-based curriculum structure, it transforms passive study logging into active, personalized learning guidance for semester exams, lab vivas, and placement/competitive-exam preparation. The platform supports five core capabilities: Study Session Tracking, Exam Readiness Prediction, AI Quiz Generation, Spaced Repetition Scheduling, and Smart Notifications.

## Glossary

- **StudyPilot**: The overall platform comprising multiple microservices that collectively deliver study tracking, quiz generation, readiness scoring, spaced repetition, and notification capabilities.
- **User_Service**: The microservice responsible for user registration, authentication, JWT issuance, profile management, and study preference configuration.
- **Curriculum_Service**: The microservice that serves as source of truth for degree program subject catalogs, semester-wise subject mappings, and unit/module breakdowns per subject.
- **Session_Service**: The microservice responsible for CRUD operations on study sessions logged against a subject and unit.
- **Quiz_Service**: The microservice responsible for generating quizzes via LLM from units, uploaded notes, previous year question papers, or weak-topic lists, including viva-style Q&A for lab subjects.
- **Repetition_Service**: The microservice implementing SM-2-based spaced repetition scheduling with exam-aware interval capping.
- **Readiness_Service**: The microservice that computes exam readiness scores (0–100) per user/subject and per unit by combining multiple performance signals.
- **Notification_Service**: The microservice responsible for daily digests, readiness drop alerts, exam countdowns, and zero-activity nudges.
- **API_Gateway**: The single entry point that handles request routing, JWT validation, rate limiting, and OpenAPI aggregation.
- **Study_Session**: A logged period of study activity associated with a specific subject, unit/module, duration, focus/energy rating, and optional notes.
- **Readiness_Score**: A numeric value (0–100) representing a student's preparedness for an exam in a given subject or unit.
- **PYQ**: Previous Year Question paper — past exam papers used for practice and quiz generation.
- **SM-2_Algorithm**: The SuperMemo 2 spaced repetition algorithm that calculates optimal review intervals based on recall quality.
- **Semester**: A fixed academic term containing a set of subjects specific to the student's degree program and current term.
- **Unit**: A subdivision of a subject's syllabus (also called module); the number of units per subject is configurable.
- **Viva_QA**: Question-and-answer format specifically designed for laboratory/practical subject oral examination preparation.
- **JWT**: JSON Web Token used for stateless authentication, consisting of access and refresh token pairs.
- **Event**: An asynchronous message published to RabbitMQ when a domain action occurs (e.g., session.logged, quiz.completed).
- **Goal_Type**: The student's preparation target — one of semester_exam, placement_prep, or competitive_exam.

## Requirements

### Requirement 1: User Registration and Authentication

**User Story:** As a college student, I want to register and securely log in to StudyPilot, so that my study data is protected and personalized to my academic profile.

#### Acceptance Criteria

1. WHEN a student submits valid registration details (email, password, college, university, degree program, current semester), THE User_Service SHALL create a user account and return a JWT access token and refresh token pair, where email must be a valid email format and unique across all accounts, password must be 8–72 characters containing at least one uppercase letter, one lowercase letter, one digit, and one special character, and text fields (college, university, degree program) must be 1–200 characters each.
2. WHEN a student submits valid login credentials, THE User_Service SHALL authenticate the student and return a JWT access token with an expiration of 15 minutes and a refresh token with an expiration of 7 days.
3. WHEN a student submits an expired access token with a valid, non-expired refresh token, THE User_Service SHALL issue a new access token without requiring re-authentication.
4. IF a student submits invalid or missing registration fields, THEN THE User_Service SHALL return a 422 response with field-level validation error messages indicating which fields failed and why, without exposing internal system details.
5. IF a student submits incorrect login credentials, THEN THE User_Service SHALL return a 401 response without revealing whether the email or password was incorrect.
6. IF a student submits a refresh token that is expired, revoked, or invalid, THEN THE User_Service SHALL return a 401 response and require the student to re-authenticate.
7. WHEN a student updates their profile (college, university, degree program, current semester, study preferences), THE User_Service SHALL validate that text fields are 1–200 characters, persist the changes, and return the updated profile.
8. THE User_Service SHALL store study preferences including daily study hours target (a numeric value from 0.5 to 16 hours) and goal type (semester_exam, placement_prep, or competitive_exam) per user.
9. IF a student fails login authentication 5 consecutive times for the same email, THEN THE User_Service SHALL temporarily lock login attempts for that email for 15 minutes and return a response indicating the account is temporarily locked.

### Requirement 2: Curriculum Management

**User Story:** As a college student, I want the platform to know my degree program's subjects and their unit breakdowns per semester, so that I can track study progress against my actual syllabus.

#### Acceptance Criteria

1. THE Curriculum_Service SHALL store degree program catalogs containing program name, university, total semesters, and semester-wise subject mappings without hardcoding any specific discipline.
2. WHEN a student requests subjects for a given degree program and semester, THE Curriculum_Service SHALL return the list of subjects with their codes, names, type (theory or lab/practical), and credit hours.
3. WHEN a student requests unit details for a given subject, THE Curriculum_Service SHALL return the ordered list of units/modules with unit number, title, and topic keywords (1–20 keywords per unit).
4. THE Curriculum_Service SHALL support a configurable number of units per subject (minimum 1, maximum 20) to accommodate varying university syllabi.
5. WHEN an administrator adds or updates a degree program catalog, THE Curriculum_Service SHALL validate that each subject has at least one unit defined (for theory subjects) and persist the catalog.
6. THE Curriculum_Service SHALL distinguish between theory subjects and lab/practical subjects so that downstream services can apply appropriate tracking strategies (units for theory, flat topic lists for lab).
7. IF a request references a program ID or subject code that does not exist, THEN THE Curriculum_Service SHALL return a 404 response with a descriptive error message.
8. IF a request to add a subject includes fewer than 1 or more than 20 units, THEN THE Curriculum_Service SHALL return a 422 response with a validation error.

### Requirement 3: Study Session Tracking

**User Story:** As a college student, I want to log my study sessions against specific subjects and units with duration and focus ratings, so that I can monitor my study habits and feed data into readiness predictions.

#### Acceptance Criteria

1. WHEN a student submits a study session with subject code, unit number, duration in minutes, focus/energy rating (1–5), and optional notes (maximum 1000 characters), THE Session_Service SHALL persist the session and publish a session.logged event to RabbitMQ.
2. WHEN a student requests their session history for a subject, THE Session_Service SHALL return only non-soft-deleted sessions ordered by most recent first, with pagination support using limit (default 20, maximum 100) and offset (default 0) parameters.
3. WHEN a student requests their session history filtered by unit number, THE Session_Service SHALL return only non-soft-deleted sessions matching that specific unit.
4. WHEN a student submits a study session, THE Session_Service SHALL validate that the subject code and unit number reference a valid entry in the Curriculum_Service before persisting the session.
5. IF a student submits a session with duration less than 1 minute or greater than 480 minutes, THEN THE Session_Service SHALL reject the request with a validation error indicating the allowed duration range.
6. IF a student submits a session with a focus/energy rating outside the integer range 1–5, THEN THE Session_Service SHALL reject the request with a validation error indicating the allowed rating range.
7. WHEN a student deletes a study session, THE Session_Service SHALL soft-delete the record (excluding it from all subsequent history queries) and publish a session.deleted event.
8. THE Session_Service SHALL include the following fields in the session.logged event payload: user_id, subject_code, unit_number, duration_minutes, focus_rating, and session_timestamp.
9. IF the Curriculum_Service is unavailable or returns an error during subject/unit validation, THEN THE Session_Service SHALL reject the session submission with an error indicating that curriculum validation could not be completed.
10. IF RabbitMQ is unavailable when publishing a session.logged or session.deleted event, THEN THE Session_Service SHALL retain the event for later delivery and return a success response to the student.

### Requirement 4: AI Quiz Generation

**User Story:** As a college student, I want to generate quizzes from my syllabus units, uploaded lecture notes, or previous year question papers, so that I can actively test my understanding rather than passively reviewing.

#### Acceptance Criteria

1. WHEN a student requests a quiz for a specific subject and unit, THE Quiz_Service SHALL generate quiz questions using the Anthropic Claude API based on the unit's topic keywords fetched from the Curriculum_Service and any previously uploaded materials for that subject-unit pair.
2. WHEN a student uploads lecture notes or a PDF (maximum file size 20 MB, supported formats: PDF, DOCX, TXT, and image files for OCR), THE Quiz_Service SHALL extract text content (using OCR for scanned documents) and associate the material with a subject and unit for future quiz generation.
3. WHEN a student uploads a previous year question paper (PYQ), THE Quiz_Service SHALL parse the document via OCR and LLM, extract individual questions, and store them tagged by subject, unit, exam year, and exam type (internal or external).
4. WHEN a student requests a quiz from a PYQ source, THE Quiz_Service SHALL generate a quiz drawing from the extracted PYQ question bank for the specified subject and unit, prioritizing questions from recent exam years.
5. WHEN a student requests a viva-style Q&A session for a lab/practical subject, THE Quiz_Service SHALL generate oral-examination-style questions with expected answer outlines rather than multiple-choice format, with each answer outline being 50–200 words.
6. WHEN a student requests a quiz targeting weak topics, THE Quiz_Service SHALL query the Readiness_Service for units with readiness scores below 50 and generate questions focused on those units.
7. WHEN a student submits quiz answers, THE Quiz_Service SHALL evaluate responses, compute a score (percentage correct), provide per-question feedback indicating the correct answer and explanation, and publish a quiz.completed event.
8. THE Quiz_Service SHALL include the following fields in the quiz.completed event payload: user_id, subject_code, unit_number, quiz_type (unit, pyq, viva, weak_topic), score_percentage, question_count, and completion_timestamp.
9. IF the Anthropic Claude API is unavailable or returns an error, THEN THE Quiz_Service SHALL return a 503 response with a retry-after header (minimum 30 seconds) and a descriptive error message without exposing internal API details.
10. THE Quiz_Service SHALL support configurable quiz length (number of questions) with a default of 10 and a maximum of 50 questions per quiz.
11. THE Quiz_Service SHALL wrap the LLM call behind a QuizGenerator interface so that the model or provider can be swapped without changing API contracts or downstream consumers.

### Requirement 5: Spaced Repetition Scheduling

**User Story:** As a college student, I want a spaced repetition system that schedules my revisions intelligently based on how well I recall material, weighted by upcoming exam dates, so that I retain knowledge efficiently.

#### Acceptance Criteria

1. THE Repetition_Service SHALL implement the SM-2 algorithm to compute review intervals based on the student's recall quality rating (0–5) for each subject-unit pair.
2. WHEN the Repetition_Service receives a quiz.completed event, THE Repetition_Service SHALL update the SM-2 parameters (easiness factor, interval, repetition count) for the corresponding subject-unit pair using the quiz score mapped to a quality rating (0–5).
3. WHEN the Repetition_Service receives a session.logged event, THE Repetition_Service SHALL record the review activity and set the next review date for the corresponding subject-unit pair by applying the SM-2 algorithm with a default quality rating of 3 (correct response with difficulty).
4. WHILE an exam date is set for a subject and fewer than 14 days remain, THE Repetition_Service SHALL cap the computed interval for each unit to no more than (days_until_exam / unreviewed_units_remaining_for_that_subject), rounded down to a minimum of 1 day, so that all units for that subject are scheduled at least once before the exam date.
5. WHEN a student requests their revision schedule, THE Repetition_Service SHALL return a prioritized list of at most 50 subject-unit pairs due for review, ordered first by exam urgency weight (subjects with an exam within 14 days whose units have not all been reviewed are ranked above non-exam items), then within each group ordered by overdue days descending (most overdue first).
6. WHILE a subject has an exam date set within 14 days, THE Repetition_Service SHALL multiply the priority score of each unreviewed unit for that subject by (1 + unreviewed_units_remaining / total_units_for_subject), so that subjects with more unreviewed units rank higher within the exam-urgent group.
7. IF a subject-unit pair has never been reviewed, THEN THE Repetition_Service SHALL assign an initial interval of 1 day and an easiness factor of 2.5.
8. WHEN a student sets or updates an exam date for a subject, THE Repetition_Service SHALL recalculate all intervals for that subject's units using the exam-aware capping rule, scheduling at most one unit per day and distributing units evenly across available days.
9. IF a student sets an exam date for a subject and the number of unreviewed units exceeds the number of days remaining before the exam, THEN THE Repetition_Service SHALL schedule multiple units per day by distributing them evenly across available days (ceiling of unreviewed_units / days_remaining per day) and shall return a notification indicating the compressed review load.

### Requirement 6: Exam Readiness Prediction

**User Story:** As a college student, I want to see a readiness score (0–100) for each subject and each unit, so that I know which areas need more attention before my exams.

#### Acceptance Criteria

1. THE Readiness_Service SHALL compute a readiness score (integer 0–100) per student per subject by combining weighted signals each normalized to 0–100: quiz accuracy (25%), PYQ practice accuracy (20%), spaced repetition review currency (20%), unit coverage percentage (15%), study session consistency (10%), and days remaining to exam (10%), where study session consistency is defined as the percentage of the last 14 days on which the student logged at least one study session for that subject.
2. WHEN the Readiness_Service receives a quiz.completed event, THE Readiness_Service SHALL recalculate the readiness score for the affected subject and unit within 30 seconds.
3. WHEN the Readiness_Service receives a session.logged event, THE Readiness_Service SHALL recalculate the readiness score for the affected subject and unit within 30 seconds.
4. WHEN a student requests readiness scores, THE Readiness_Service SHALL return per-subject scores and per-unit breakdown scores for all subjects in the student's current semester within 2 seconds.
5. THE Readiness_Service SHALL cache computed readiness scores in Redis with a time-to-live of 5 minutes to serve repeated requests without recomputation.
6. THE Readiness_Service SHALL publish a readiness.updated event containing user_id, subject_code, unit_number, previous_score, new_score, and computation_timestamp after each recalculation.
7. IF a subject has no exam date set, THEN THE Readiness_Service SHALL compute the score with the days-remaining component set to a neutral value of 50 (out of 100 for that signal).
8. WHEN the student's goal type is placement_prep or competitive_exam, THE Readiness_Service SHALL compute readiness using adjusted weights: quiz accuracy (25%), PYQ practice accuracy (30%), spaced repetition review currency (20%), unit coverage percentage (15%), study session consistency (10%), and days remaining to exam (0%).
9. IF a signal has no data for a given subject or unit (zero quizzes attempted, zero PYQ sessions, or zero study sessions logged), THEN THE Readiness_Service SHALL exclude that signal from the computation and redistribute its weight proportionally among the remaining signals that have data.
10. IF all signals for a subject or unit have no data, THEN THE Readiness_Service SHALL return a readiness score of 0 and indicate that insufficient data is available for that subject or unit.

### Requirement 7: Smart Notifications

**User Story:** As a college student, I want to receive daily revision plans, alerts when my readiness drops, and exam countdown reminders, so that I stay on track without manually checking the platform.

#### Acceptance Criteria

1. THE Notification_Service SHALL generate a daily study digest for each active student (defined as a student who has logged at least one study session or login within the past 14 days) containing: subjects due for review today, current readiness scores for upcoming exams, and suggested study duration per subject. THE Notification_Service SHALL deliver the digest at the student's configured preferred delivery time, or at 08:00 local time if no preference is set.
2. WHEN the Notification_Service receives a readiness.updated event where the new score is more than 10 points below the previous score, THE Notification_Service SHALL send a readiness drop alert to the affected student within 5 minutes, specifying the subject name, previous score, and new score.
3. WHILE an exam date is set and fewer than 7 days remain, THE Notification_Service SHALL send a daily exam countdown notification to the student specifying the subject and days remaining. THE Notification_Service SHALL NOT also send the weekly countdown notification for that same exam during this period.
4. WHILE an exam date is set and 7 or more days remain but fewer than 30 days remain, THE Notification_Service SHALL send a weekly exam countdown notification to the student specifying the subject and days remaining.
5. IF a student has logged zero study sessions in the past 48 hours, THEN THE Notification_Service SHALL send a zero-activity nudge containing the student's next recommended subject and estimated session duration. THE Notification_Service SHALL send at most one zero-activity nudge per 48-hour period per student.
6. WHEN a student configures notification preferences (enabled/disabled per notification type, preferred delivery time), THE Notification_Service SHALL respect those preferences for all future notifications. IF a student has not configured preferences, THEN THE Notification_Service SHALL deliver all notification types as enabled with a default delivery time of 08:00 local time.
7. THE Notification_Service SHALL deliver notifications via in-app message queue; integration with email or push notification providers SHALL be supported through a pluggable delivery adapter interface.
8. IF the Notification_Service fails to deliver a notification through the selected channel, THEN THE Notification_Service SHALL retry delivery up to 3 times with exponential backoff (delays of 1 minute, 5 minutes, and 15 minutes), and SHALL log the failure in the notification_log after all retries are exhausted.
9. THE Notification_Service SHALL NOT send more than 10 notifications per student per calendar day across all notification types, excluding notifications triggered by explicit student actions.

### Requirement 8: API Gateway and Routing

**User Story:** As a client application developer, I want a single API entry point that handles authentication, routing, and rate limiting, so that I can interact with StudyPilot through a unified interface.

#### Acceptance Criteria

1. THE API_Gateway SHALL route incoming requests to the appropriate downstream microservice based on URL path prefix mapping, adding no more than 200ms of gateway-processing latency to the downstream service response time.
2. WHEN a request arrives with a valid JWT in the Authorization header, THE API_Gateway SHALL extract the user identity and forward the request to the downstream service with headers containing the authenticated user's ID and role.
3. IF a request arrives without a JWT or with an invalid/expired JWT on a non-public endpoint (where public endpoints are limited to registration and login paths), THEN THE API_Gateway SHALL return a 401 response without forwarding to any downstream service.
4. IF an authenticated user exceeds 100 requests within a sliding 60-second window, THEN THE API_Gateway SHALL return a 429 response with a Retry-After header indicating the number of seconds until the next request is permitted.
5. THE API_Gateway SHALL expose an aggregated OpenAPI specification combining the documentation from all downstream services.
6. THE API_Gateway SHALL expose a consolidated /health endpoint that reports each downstream service as "healthy" or "unhealthy" based on a per-service health check with a timeout of 5 seconds, and SHALL report the overall gateway status as "healthy" only when all downstream services are healthy.
7. IF a downstream service is unreachable or does not respond within 10 seconds, THEN THE API_Gateway SHALL return a 502 response with an error indication that the requested service is temporarily unavailable.

### Requirement 9: Event-Driven Communication

**User Story:** As a platform architect, I want services to communicate asynchronously via events with guaranteed delivery and idempotency, so that the system remains loosely coupled and resilient to transient failures.

#### Acceptance Criteria

1. THE StudyPilot platform SHALL use RabbitMQ as the message broker for all asynchronous inter-service events.
2. THE StudyPilot platform SHALL define event schemas using JSON Schema in a shared events package, and all published events SHALL conform to their registered schema.
3. WHEN a service publishes an event, THE publishing service SHALL include a unique event_id (UUID), event_type, timestamp, correlation_id (UUID for distributed tracing), and payload conforming to the event's JSON Schema.
4. WHEN a service consumes an event, THE consuming service SHALL check the event_id against a deduplication table and skip processing if the event has already been handled (idempotent consumption), and THE consuming service SHALL retain deduplication entries for a minimum of 7 days before they are eligible for removal.
5. IF a consumer fails to process an event, THEN THE consuming service SHALL retry processing up to 3 times with exponential backoff starting at a base delay of 1 second (delays of 1s, 2s, 4s) before routing the event to a dead-letter queue.
6. THE StudyPilot platform SHALL support the following event types: session.logged, session.deleted, quiz.completed, readiness.updated.
7. IF a publishing service attempts to publish an event that does not conform to its registered JSON Schema, THEN THE publishing service SHALL reject the event without sending it to the broker and SHALL return an error indicating a schema validation failure.

### Requirement 10: Observability and Health Monitoring

**User Story:** As a platform operator, I want structured logging, health endpoints, metrics, and distributed tracing across all services, so that I can monitor system health and diagnose issues quickly.

#### Acceptance Criteria

1. THE StudyPilot platform SHALL emit all application logs in structured JSON format containing timestamp (ISO 8601), service name, log level (one of DEBUG, INFO, WARNING, ERROR, CRITICAL), correlation_id, and message fields.
2. WHEN a service receives a request, THE service SHALL generate or propagate a correlation_id (W3C Trace Context format) across all downstream calls and event publications for distributed tracing.
3. THE StudyPilot platform SHALL expose /health and /ready endpoints on each microservice, where /health returns HTTP 200 with a JSON body containing a "status" field set to "healthy" when the service process is running, and /ready returns HTTP 200 with a JSON body containing a "status" field set to "ready" when all dependencies (database connectivity, message broker connectivity) respond within 5 seconds.
4. IF a readiness dependency (database or message broker) fails to respond within 5 seconds, THEN THE /ready endpoint SHALL return HTTP 503 with a JSON body containing a "status" field set to "not_ready" and a "dependencies" field listing each dependency and its availability status.
5. THE StudyPilot platform SHALL expose Prometheus-compatible /metrics endpoints on each microservice reporting request count, request latency histograms (with buckets at 10ms, 50ms, 100ms, 250ms, 500ms, 1s, 5s, and 10s), and error rates partitioned by HTTP status code class (4xx, 5xx).
6. THE StudyPilot platform SHALL export distributed trace spans via OpenTelemetry SDK to a configured collector for all synchronous REST calls and asynchronous event processing, where each span includes service name, operation name, duration, and status code.
7. WHEN the configured trace collector is unavailable, THE service SHALL continue processing requests without interruption and SHALL buffer or discard trace spans without affecting request latency by more than 50ms.

### Requirement 11: Data Persistence and Migration

**User Story:** As a platform architect, I want each service to own its database schema with versioned migrations, so that services remain independently deployable and schema changes are traceable.

#### Acceptance Criteria

1. THE StudyPilot platform SHALL provision a separate MySQL 8 schema for each microservice (database-per-service pattern) with no cross-service joins.
2. WHEN a service needs to access data owned by another service, THE requesting service SHALL call the owning service's REST API or consume events via RabbitMQ rather than querying the other service's database directly.
3. THE StudyPilot platform SHALL use Alembic for database schema migrations, with each service maintaining its own independent migration history and each migration file identified by a sequential revision identifier.
4. WHEN a new migration is created for a service, THE migration SHALL include both upgrade and downgrade functions, and the upgrade function SHALL preserve existing data in affected tables unless the migration explicitly documents a destructive change.
5. THE StudyPilot platform SHALL use Redis for caching session tokens with a TTL of 24 hours, readiness score caches with a TTL of 5 minutes, and rate limiting counters with a sliding window of 60 seconds and a maximum of 100 requests per window per client.
6. IF Redis becomes unavailable, THEN THE StudyPilot platform SHALL continue processing requests without caching, bypass rate limiting, and log an error indicating the Redis connection failure.

### Requirement 12: Containerization and Deployment

**User Story:** As a DevOps engineer, I want all services containerized with local docker-compose and production Kubernetes manifests, so that the platform is portable and consistently deployable across environments.

#### Acceptance Criteria

1. THE StudyPilot platform SHALL provide a Dockerfile for each microservice following multi-stage build pattern (build stage + runtime stage) with Python 3.12 base image, where the final runtime image does not exceed 200 MB uncompressed size.
2. THE StudyPilot platform SHALL provide a docker-compose.yml file that starts all microservices, MySQL, Redis, and RabbitMQ for local development with a single command, with service dependency ordering ensuring database and broker containers report healthy before application containers start.
3. THE StudyPilot platform SHALL provide Kubernetes manifests (Deployment, Service, ConfigMap, Secret) for each microservice for production deployment, with each Deployment specifying a minimum of 2 replicas, a liveness probe, and a readiness probe.
4. WHEN a developer runs docker-compose up, THE platform SHALL start all services with health checks passing within 60 seconds, where each service health check verifies connectivity to its required database and message broker and responds with HTTP 200 on the service health endpoint.
5. THE StudyPilot platform SHALL configure each service via environment variables for all deployment-sensitive values (database URLs, API keys, broker URLs, secret keys).
6. IF a required dependency (MySQL, Redis, or RabbitMQ) is unreachable during container startup, THEN THE service SHALL fail its readiness check and not accept traffic until the dependency becomes available, retrying the connection at 5-second intervals for a maximum of 10 attempts before the container restarts.
7. IF a required dependency becomes unreachable after a service has started, THEN THE service SHALL fail its liveness probe within 30 seconds, triggering a container restart.

### Requirement 13: Testing and Quality Assurance

**User Story:** As a developer, I want a comprehensive testing strategy with unit tests, contract tests, and integration tests, so that I can confidently deploy changes without breaking cross-service contracts.

#### Acceptance Criteria

1. THE StudyPilot platform SHALL use pytest as the test framework for all microservices.
2. THE StudyPilot platform SHALL maintain unit tests for service layer logic, repository layer logic, and utility functions with mocked database and external service dependencies, achieving minimum 80% line coverage per service as measured by a coverage reporting tool.
3. IF a service's unit test coverage falls below 80% line coverage, THEN THE StudyPilot platform SHALL fail the CI/CD pipeline build for that service and prevent progression to subsequent stages.
4. THE StudyPilot platform SHALL maintain contract tests that validate each published event payload against its corresponding JSON Schema definition in the shared events package, and report which schema constraints were violated on validation failure.
5. THE StudyPilot platform SHALL maintain integration tests that exercise API endpoints with real MySQL test container and RabbitMQ connections provisioned via docker-compose test environment.
6. THE StudyPilot platform SHALL run a CI/CD pipeline per service consisting of sequential stages: lint (ruff) → unit test → contract test → build Docker image → deploy.
7. IF any stage in the CI/CD pipeline fails, THEN THE StudyPilot platform SHALL halt the pipeline for that service, prevent execution of subsequent stages, and report the failed stage name and failure reason.
