"""
FastAPI Backend - Clean Layered Architecture

OVERVIEW
========
This backend follows a classic 4-layer architecture that enforces clear separation
of concerns and enables independent testing of each layer.

Dependencies flow ONLY downward:
    API Request
        ↓
    routers/ (HTTP Layer)
        ↓
    services/ (Business Logic Layer)
        ↓
    repositories/ (Data Access Layer)
        ↓
    models/ + core/ (Data & Infrastructure)


LAYER RESPONSIBILITIES
======================

1. ROUTERS (routers/)
   ─────────────────
   PURPOSE: Handle HTTP-only concerns
   
   RESPONSIBILITIES:
   - Parse and validate HTTP requests (Pydantic schemas)
   - Dependency injection (FastAPI Depends)
   - Call service layer with validated data
   - Convert service responses to API response schemas
   - Return HTTP responses with correct status codes
   
   MUST NOT:
   - Contain business logic
   - Execute SQL queries directly
   - Create database sessions
   - Import models directly (use schemas instead)
   - Make authorization decisions (except auth routes)
   
   EXAMPLE:
   --------
   @router.post("/submit")
   def submit_feedback(
       request: FeedbackSubmitRequest,                 # Validated request
       current_user = Depends(get_current_user),       # Dependency injection
       session: Session = Depends(get_session),        # Dependency injection
   ):
       repo = FeedbackRepository(session)
       service = FeedbackService(repo)
       feedback = service.submit_feedback(...)         # Call service
       return FeedbackResponse.from_orm(feedback)      # Return schema


2. SERVICES (services/)
   ────────────────────
   PURPOSE: Implement business logic
   
   RESPONSIBILITIES:
   - Validate business rules
   - Orchestrate repositories
   - Apply authorization logic
   - Transform data between API schemas and persistence models
   
   MUST NOT:
   - Create database sessions (receive via DI)
   - Import FastAPI
   - Handle HTTP directly
   - Return HTTP responses
   - Expose persistence models in public methods
   
   EXAMPLE:
   --------
   class FeedbackService:
       def __init__(self, feedback_repo: FeedbackRepository):
           self.feedback_repo = feedback_repo
       
       def submit_feedback(self, user_id: int, content: str):
           # Business logic: validate, maybe check permissions
           feedback = Feedback(user_id=user_id, content=content)
           return self.feedback_repo.save_feedback(feedback)


3. REPOSITORIES (repositories/)
   ───────────────────────────
   PURPOSE: Abstract database access
   
   RESPONSIBILITIES:
   - CRUD operations (Create, Read, Update, Delete)
   - Execute SQLModel queries
   - Translate database errors to domain errors
   
   MUST NOT:
   - Contain business logic
   - Import FastAPI
   - Create sessions
   - Return Pydantic schemas
   
   EXAMPLE:
   --------
   class FeedbackRepository:
       def __init__(self, session: Session):
           self.session = session
       
       def save_feedback(self, feedback: Feedback) -> Feedback:
           self.session.add(feedback)
           self.session.commit()
           self.session.refresh(feedback)
           return feedback


4. MODELS (models/)
   ───────────────
   PURPOSE: Define persistence layer
   
   RESPONSIBILITIES:
   - SQLModel definitions with table=True
   - Define database schema
   - Pydantic validation for stored data
   
   MUST NOT:
   - Be exposed directly in API responses
   - Contain business logic
   - Be used for API request validation
   
   EXAMPLE:
   --------
   class User(SQLModel, table=True):
       id: Optional[int] = Field(default=None, primary_key=True)
       username: str = Field(index=True, unique=True)
       hashed_password: str


5. SCHEMAS (schemas/)
   ──────────────────
   PURPOSE: Define API contracts
   
   RESPONSIBILITIES:
   - Request validation (Pydantic)
   - Response serialization
   - Hide internal DB fields from clients
   - Separate read/write models when needed
   
   MUST NOT:
   - Have database table definitions
   - Import models directly in public API
   
   STRUCTURE:
   - UserRegisterRequest: What the client sends
   - UserLoginRequest: What the client sends
   - UserResponse: What the API returns (no hashed_password)
   
   EXAMPLE:
   --------
   class UserResponse(BaseModel):
       id: int
       username: str
       # Note: hashed_password NOT included
       
       class Config:
           from_attributes = True  # SQLModel → Pydantic


6. CORE (core/)
   ────────────
   PURPOSE: Infrastructure and shared utilities
   
   RESPONSIBILITIES:
   - Database engine and session factory
   - Security helpers (password hashing, JWT stubs)
   - Configuration management
   - Shared dependencies
   
   FILES:
   - core/database.py: Engine, create_db_and_tables(), get_session()
   - core/security.py: hash_password(), verify_password(), get_current_user()


DEPENDENCY INJECTION PATTERN
============================

FastAPI's Depends() is used consistently:

   from fastapi import Depends
   
   @router.post("/feedback")
   def submit_feedback(
       request: FeedbackSubmitRequest,
       current_user = Depends(get_current_user),        # Auth stub
       session: Session = Depends(get_session),         # DB session
   ):
       # Dependencies are automatically injected
       repo = FeedbackRepository(session)
       service = FeedbackService(repo)
       # ... rest of handler


AUTHENTICATION DESIGN (Future JWT)
==================================

CURRENT STATE: Stubbed with get_current_user()
   Returns a fake CurrentUserStub object
   Allows testing without auth infrastructure

FUTURE JWT MIGRATION:
   1. Update core/security.py get_current_user()
   2. Extract JWT token from Authorization header
   3. Validate token signature and expiration
   4. Return real User object
   5. No changes needed in routers, services, or repositories!

This design allows auth to be added later without touching business logic.


DATA FLOW EXAMPLE: Submit Feedback
===================================

1. CLIENT sends POST /feedback/submit with body:
   {
     "content": "The UI is confusing",
     "category": "UX"
   }

2. ROUTER receives request:
   - Pydantic validates against FeedbackSubmitRequest
   - Depends injection provides session and current_user
   - Creates FeedbackRepository and FeedbackService
   - Calls service.submit_feedback()

3. SERVICE executes business logic:
   - Creates Feedback(user_id, content, category)
   - Calls repo.save_feedback()

4. REPOSITORY saves to database:
   - session.add(feedback)
   - session.commit()
   - Returns Feedback persistence model

5. ROUTER converts response:
   - FeedbackResponse.from_orm(feedback)
   - Returns JSON to client

6. CLIENT receives response:
   {
     "id": 42,
     "user_id": 1,
     "content": "The UI is confusing",
     "category": "UX"
   }


TESTING IMPLICATIONS
====================

This architecture enables:

- Unit test services without DB (mock repository)
- Unit test repositories with test DB session
- Unit test routers without FastAPI TestClient (mock dependencies)
- Full integration tests with real DB

Example:
   def test_submit_feedback():
       # Mock the repository
       mock_repo = MagicMock(spec=FeedbackRepository)
       service = FeedbackService(mock_repo)
       
       result = service.submit_feedback(user_id=1, content="Test")
       
       mock_repo.save_feedback.assert_called_once()


MIGRATION CHECKLIST
===================

When adding a new feature:

□ Define persistence model in models/
□ Define request/response schemas in schemas/
□ Create repository methods in repositories/
□ Add business logic to services/
□ Create router endpoints in routers/
□ Import from core/ not utils/
□ Inject dependencies via Depends()
□ Never expose SQLModel directly

When refactoring existing code:

□ Move business logic to services/
□ Move SQL to repositories/
□ Create request/response schemas
□ Update routers to use DI pattern
□ Add docstrings explaining layer responsibility
□ Test each layer independently
"""
