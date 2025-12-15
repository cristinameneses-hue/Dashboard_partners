"""
Presentation Layer

This layer handles all external communication including:
- REST API endpoints (FastAPI)
- Request/response validation (Pydantic)
- Authentication and authorization
- Rate limiting and security
- Health checks and monitoring

The presentation layer depends on the application layer (use cases)
but knows nothing about the infrastructure details.

Following Clean Architecture principles:
- Presentation layer is independent of database
- Presentation layer is independent of external services
- Presentation layer only handles HTTP/API concerns
"""