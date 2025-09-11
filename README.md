# 🚀 ERP MIF Maroc — Backend API

<p align="center">
  <em>Modern Industrial Intervention Management System</em>
</p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/python-3.11+-blue.svg"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.116-009688.svg"></a>
  <a href="https://www.sqlalchemy.org/"><img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.0-red.svg"></a>
  <a href="https://www.postgresql.org/"><img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-336791.svg"></a>
  <a href="https://www.docker.com/"><img alt="Docker" src="https://img.shields.io/badge/Docker-ready-2496ED.svg"></a>
  <a href="#api-documentation"><img alt="OpenAPI" src="https://img.shields.io/badge/OpenAPI-3.0-green.svg"></a>
  <a href="https://github.com/Rochdi112/FastApi_ERP_BackEnd_MIF_Maroc/actions"><img alt="Tests" src="https://img.shields.io/badge/tests-passing-brightgreen.svg"></a>
  <a href="#coverage"><img alt="Coverage" src="https://img.shields.io/badge/coverage-89.24%-orange.svg"></a>
</p>

---

## 📋 Table of Contents

- [📖 Overview](#-overview)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [📁 Project Structure](#-project-structure)
- [🛠️ Technology Stack](#️-technology-stack)
- [⚡ Quick Start](#-quick-start)
- [🔧 Installation & Setup](#-installation--setup)
- [🗄️ Database](#️-database)
- [🔗 API Documentation](#-api-documentation)
- [🧪 Testing](#-testing)
- [🚀 Deployment](#-deployment)
- [🔒 Security](#-security)
- [📊 Monitoring](#-monitoring)
- [🛠️ Development](#️-development)
- [❓ Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 📖 Overview

**ERP MIF Maroc Backend** is a robust, production-ready API built with **FastAPI** for comprehensive industrial intervention management. The system provides a complete REST API with JWT authentication, role-based access control (RBAC), and modular architecture designed for scalability.

### 🎯 Use Cases

- Industrial equipment management and tracking
- Maintenance intervention planning and monitoring
- Technician resource management
- Automated notification systems
- Document management and file uploads
- Reporting and analytics

---

## ✨ Features

### 🔐 Authentication & Authorization
- **JWT Authentication** with access and refresh tokens
- **RBAC (Role-Based Access Control)** with 4 roles:
  - `admin`: Full system access
  - `responsable`: Intervention and technician management
  - `technicien`: Intervention execution
  - `client`: Limited access to related interventions
- **Password security** with bcrypt hashing

### 👥 User Management
- Complete CRUD operations for users
- Profile and role management
- Email/username authentication
- Secure password changes

### 🔧 Equipment Management
- Industrial equipment catalog
- Maintenance frequency tracking
- Location and equipment type management
- Intervention history

### 👨‍🔧 Technician Management
- Technician profiles and specializations
- Skills and competencies tracking
- Availability and scheduling
- Intervention assignments

### 📋 Intervention Management
- Intervention creation and tracking
- Status management: `ouverte`, `en_cours`, `cloturee`, `annulee`
- Priority levels: `normale`, `haute`, `critique`
- Types: `corrective`, `preventive`, `curative`
- Deadline management and urgency handling

### 📅 Planning
- Automated intervention scheduling
- Scheduled task generation
- Reminder notifications
- Resource optimization

### 📄 Document Management
- File upload and storage
- Intervention associations
- Secure downloads
- Attachment management

### 🔔 Notifications
- Real-time notification system
- Email notifications
- Customizable templates
- Notification history

### 📊 Reports & Analytics
- Report generation
- Intervention statistics
- KPIs and metrics
- Data export capabilities

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Monitoring    │
│   (React/Vue)   │◄──►│   (FastAPI)     │◄──►│   (Prometheus)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Services      │    │   Database      │    │   Cache/Queue   │
│   Layer         │◄──►│   (PostgreSQL)  │◄──►│   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   Email Service │    │   Scheduler     │
│   (Local/Disk)  │    │   (SMTP)        │    │   (APScheduler) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🏛️ Technical Architecture

- **API Layer**: FastAPI with OpenAPI 3.0
- **Business Logic**: Modular services
- **Data Layer**: SQLAlchemy ORM with Alembic migrations
- **Security**: JWT + RBAC + CORS
- **Background Jobs**: APScheduler for scheduled tasks
- **File Storage**: Local upload system with static access
- **Notifications**: FastAPI-Mail for emails
- **Monitoring**: Health endpoints and metrics

---

## 📁 Project Structure

```
PFE_ERP_BackEnd_MIF_Maroc/
├── app/                          # Main application code
│   ├── main.py                   # FastAPI main application
│   ├── core/                     # Core configuration and utilities
│   │   ├── config.py            # Pydantic configuration
│   │   ├── security.py          # JWT security utilities
│   │   ├── rbac.py             # Role-based access control
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging.py          # Logging configuration
│   ├── api/v1/                 # API v1 endpoints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── users.py           # User management
│   │   ├── techniciens.py     # Technician management
│   │   ├── equipements.py     # Equipment management
│   │   ├── interventions.py   # Intervention management
│   │   ├── planning.py        # Planning endpoints
│   │   ├── documents.py       # Document management
│   │   ├── notifications.py   # Notification system
│   │   ├── filters.py         # Search and filters
│   │   ├── dashboard.py       # Dashboard data
│   │   └── health.py          # Health checks
│   ├── db/                    # Database configuration
│   │   ├── database.py        # SQLAlchemy engine
│   │   └── init_db.py         # Database initialization
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py           # User model
│   │   ├── technicien.py     # Technician model
│   │   ├── equipement.py     # Equipment model
│   │   ├── intervention.py   # Intervention model
│   │   ├── document.py       # Document model
│   │   ├── notification.py   # Notification model
│   │   ├── planning.py       # Planning model
│   │   ├── historique.py     # History model
│   │   ├── contrat.py        # Contracts model
│   │   ├── stock.py          # Stock management
│   │   ├── report.py         # Reports model
│   │   └── client.py         # Client model
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py           # User schemas
│   │   ├── technicien.py     # Technician schemas
│   │   ├── equipement.py     # Equipment schemas
│   │   ├── intervention.py   # Intervention schemas
│   │   └── ...               # Other schemas
│   ├── services/             # Business logic services
│   │   ├── auth_service.py   # Authentication service
│   │   ├── user_service.py   # User service
│   │   ├── equipement_service.py # Equipment service
│   │   ├── intervention_service.py # Intervention service
│   │   ├── technicien_service.py # Technician service
│   │   ├── document_service.py # Document service
│   │   ├── notification_service.py # Notification service
│   │   └── planning_service.py # Planning service
│   ├── tasks/                # Scheduled tasks
│   │   ├── scheduler.py      # Scheduler configuration
│   │   ├── notification_tasks.py # Notification tasks
│   │   └── init.py           # Initialization
│   ├── seed/                 # Demo data
│   │   └── seed_data.py      # Seed script
│   └── static/               # Static files
│       └── uploads/          # User uploads
├── templates/                # Email templates
│   ├── notification_affectation.html
│   ├── notification_alerte.html
│   ├── notification_cloture.html
│   └── notification_information.html
├── tests/                    # Unit and integration tests
│   ├── conftest.py          # Test configuration
│   ├── api/                 # API tests
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── scripts/                 # Utility scripts
│   ├── openapi_export.py    # OpenAPI export
│   ├── validate_env.py      # Environment validation
│   ├── e2e_smoke.py         # End-to-end smoke tests
│   └── list_routes.py       # Route listing
├── deploy/                  # Deployment configuration
│   └── nginx.sample.conf    # Nginx configuration
├── monitoring/              # Monitoring setup
│   └── prometheus.yml       # Prometheus configuration
├── docker-compose.yml       # Docker Compose
├── docker-compose.prod.yml  # Production Docker Compose
├── Dockerfile              # Application Dockerfile
├── Dockerfile.prod         # Production Dockerfile
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project configuration
├── pytest.ini             # Test configuration
├── alembic.ini            # Alembic configuration
├── Makefile               # Make commands
├── .env.example           # Environment example
└── README.md              # This documentation
```

---

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy 2.0** - Python ORM for database operations
- **Pydantic v2** - Data validation and serialization
- **Alembic** - Database migration tool
- **PostgreSQL** - Relational database
- **Redis** - Cache and message queue

### Security
- **JWT (JSON Web Tokens)** - Stateless authentication
- **bcrypt** - Password hashing
- **CORS** - Cross-Origin Resource Sharing
- **RBAC** - Role-Based Access Control

### Development Tools
- **Uvicorn** - High-performance ASGI server
- **pytest** - Testing framework
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Code linting
- **coverage** - Code coverage analysis

### Deployment
- **Docker** - Containerization
- **Docker Compose** - Service orchestration
- **Nginx** - Reverse proxy and load balancing

### Communication
- **FastAPI-Mail** - Email sending
- **APScheduler** - Task scheduling

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Docker Desktop
- Git

### 🚀 Docker Start (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/Rochdi112/FastApi_ERP_BackEnd_MIF_Maroc.git
cd PFE_ERP_BackEnd_MIF_Maroc

# 2. Create environment file
cp .env.example .env

# 3. Start with Docker Compose
docker compose up --build -d

# 4. Verify the application is running
curl http://localhost:8000/health
```

The application will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 🖥️ Local Start (Windows PowerShell)

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Start PostgreSQL with Docker
docker compose up -d db

# 4. Apply database migrations
alembic upgrade head

# 5. Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 🛠️ VS Code Start

Use integrated VS Code tasks:

1. **Python: Create venv & Install** - Creates virtual environment and installs dependencies
2. **DB: Alembic upgrade head** - Applies database migrations
3. **Dev: Run FastAPI (reload)** - Starts the application in development mode

---

## 🔧 Installation & Setup

### Environment Variables

Create a `.env` file in the project root:

```env
# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
LOG_LEVEL=INFO

# PostgreSQL Database
POSTGRES_DB=erp_db
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# SMTP Email
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=user
SMTP_PASSWORD=password
EMAILS_FROM_EMAIL=no-reply@example.com

# Upload Directory
UPLOAD_DIRECTORY=app/static/uploads

# CORS
CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

# Scheduler
ENABLE_SCHEDULER=false
```

### Configuration Validation

```bash
python scripts/validate_env.py
```

---

## 🗄️ Database

### Alembic Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Migration description"

# Check migration status
alembic current
```

### Demo Data

```bash
# Populate database with test data
python -c "from app.seed.seed_data import seed_database; seed_database()"
```

---

## 🔗 API Documentation

### Main Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/health` | GET | System health status | Not required |
| `/auth/token` | POST | JWT authentication | Not required |
| `/auth/me` | GET | Current user profile | Required |
| `/users/` | GET/POST | User management | Admin required |
| `/equipements/` | GET/POST | Equipment management | Required |
| `/interventions/` | GET/POST | Intervention management | Required |
| `/techniciens/` | GET/POST | Technician management | Required |
| `/documents/` | POST | Document upload | Required |
| `/notifications/` | GET/POST | Notification management | Required |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### OpenAPI Export

```bash
# Full export (recommended)
python scripts/openapi_export_runtime.py

# Approximate export (fallback)
python scripts/openapi_export.py
```

The `openapi.json` file will be generated in the project root.

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Tests with coverage
pytest --cov=app --cov-report=html

# Specific tests
pytest tests/api/test_auth_api.py
pytest tests/unit/test_models.py

# Verbose tests
pytest -v
```

### Code Coverage

The project maintains code coverage above **80%**:

- **Current Coverage**: 89.24%
- **HTML Report**: `htmlcov/index.html`
- **XML Report**: `coverage.xml`

### Test Structure

```
tests/
├── conftest.py              # Common test configuration
├── api/                     # API tests
│   ├── test_auth_api.py
│   ├── test_users_api.py
│   ├── test_equipements_api.py
│   └── ...
├── unit/                    # Unit tests
│   ├── test_services.py
│   ├── test_models.py
│   └── ...
└── integration/             # Integration tests
    └── test_workflows.py
```

---

## 🚀 Deployment

### Production with Docker

```bash
# Build and deploy
docker compose -f docker-compose.prod.yml up --build -d

# Verify
docker compose -f docker-compose.prod.yml logs -f
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Production Environment Variables

```env
ENV=production
SECRET_KEY=your-production-secret-key
POSTGRES_HOST=your-production-db-host
POSTGRES_PASSWORD=your-production-db-password
CORS_ALLOW_ORIGINS=["https://your-frontend-domain.com"]
```

---

## 🔒 Security

### JWT Authentication

```python
# Usage example
import httpx

# Get token
response = httpx.post("http://localhost:8000/auth/token", data={
    "username": "admin@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Use token
headers = {"Authorization": f"Bearer {token}"}
response = httpx.get("http://localhost:8000/users/me", headers=headers)
```

### Access Control

The system implements role-based access control:

- **Public**: `/health`, `/docs`, `/auth/token`
- **Authenticated**: User profile, related interventions
- **Technicien**: Intervention status modifications
- **Responsable**: Technician and equipment management
- **Admin**: Full system access

### Security Best Practices

- ✅ **Hashed passwords** with bcrypt + strong policy (≥10 chars, mixed case, numbers, symbols)
- ✅ **Short JWT tokens** (15 min) with rotating refresh tokens (7 days)
- ✅ **AES-256 encryption** for documents using Fernet
- ✅ **Rate limiting** (120 req/min/IP) and Nginx security headers
- ✅ **Input validation** with Pydantic
- ✅ **CSRF protection** and strict CORS
- ✅ **Audit logs** and automated PostgreSQL backups
- ✅ **Secure CI/CD** with Bandit, Safety, pip-audit scans

### Go-Prod Status ✅

The backend meets all Go-Prod criteria from the technical audit:

- **Authentication**: JWT with rotating refresh tokens
- **Encryption**: Documents encrypted AES-256 at rest
- **Performance**: < 2s p95 response with 100 users
- **Security**: HSTS, CSP, active rate limiting headers
- **Backups**: Automated PostgreSQL with rotation
- **Monitoring**: Operational Prometheus/Grafana
- **CI/CD**: Tests ≥80%, linting, security audits

---

## 📊 Monitoring

### Health Endpoints

```bash
# Basic health
GET /health
# {"status": "ok", "timestamp": "2025-08-29T19:00:00Z", "service": "ERP MIF Maroc"}

# Detailed health
GET /health/detailed
# Complete DB, cache, system information

# Prometheus metrics
GET /metrics
# System and application metrics
```

### Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'erp-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Logging

Logs are configured with customizable levels:

- **DEBUG**: Detailed development information
- **INFO**: General operational information
- **WARNING**: Potential problem warnings
- **ERROR**: Non-blocking application errors
- **CRITICAL**: Critical errors

---

## 🛠️ Development

### Useful Commands

```bash
# Install dependencies
make install

# Validate environment
make validate

# Run database migrations
make migrate

# Start server
make serve

# Format code
make format

# Lint code
make lint

# Generate report
make report

# Build Docker
make docker-build

# Run Docker
make docker-run
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Automatic code formatting
- **isort**: Automatic import sorting
- **flake8**: Style error detection
- **mypy**: Type checking (optional)

### Commit Structure

```
feat: add feature X
fix: fix bug Y
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: maintenance tasks
```

---

## ❓ Troubleshooting

### Common Issues

#### 1. Database Connection Error

```bash
# Check PostgreSQL is running
docker compose ps

# Restart database
docker compose restart db

# Check logs
docker compose logs db
```

#### 2. Alembic Migration Error

```bash
# Ensure PostgreSQL is accessible locally
docker compose up -d db

# Check connection
python -c "from app.db.database import engine; print('OK' if engine else 'Error')"

# Reset migrations if necessary
alembic downgrade base
alembic upgrade head
```

#### 3. File Upload Issues

```bash
# Check directory permissions
ls -la app/static/uploads/

# Create directory if missing
mkdir -p app/static/uploads

# Check configuration
python -c "from app.core.config import settings; print(settings.UPLOAD_DIRECTORY)"
```

#### 4. CORS Errors

```bash
# Check CORS configuration
python -c "from app.core.config import settings; print(settings.CORS_ALLOW_ORIGINS)"

# Add frontend origin if needed
# In .env: CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

#### 5. Failing Tests

```bash
# Clean test environment
docker compose down -v

# Restart services
docker compose up -d db

# Rerun tests
pytest -v
```

### Debug Logs

```bash
# Application logs
docker compose logs app

# Real-time logs
docker compose logs -f app

# Database logs
docker compose logs db
```

---

## 🤝 Contributing

### Contribution Process

1. **Fork** the project
2. **Clone** your fork: `git clone https://github.com/your-username/PFE_ERP_BackEnd_MIF_Maroc.git`
3. **Create** a branch: `git checkout -b feature/new-feature`
4. **Commit** your changes: `git commit -m 'feat: add new feature'`
5. **Push** to your fork: `git push origin feature/new-feature`
6. **Create** a Pull Request

### Code Standards

- Follow PEP 8
- Use type hints
- Write tests for new features
- Maintain >80% code coverage
- Document complex functions

### Required Tests

Before submitting a PR:

```bash
# Run all tests
pytest

# Check coverage
pytest --cov=app --cov-report=term-missing

# Lint checks
make lint

# Format code
make format
```

---

## 📄 License

**© 2025 MIF Maroc — All rights reserved**

This project is developed by **MIF Maroc** for industrial intervention management.

### Usage Terms

- Internal use authorized for MIF Maroc
- Modifications and distribution subject to authorization
- Contact: [contact@mif-maroc.com](mailto:contact@mif-maroc.com)

---

## 📞 Support

For questions or issues:

- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/Rochdi112/FastApi_ERP_BackEnd_MIF_Maroc/issues)
- **Email**: support@mif-maroc.com

---

<p align="center">
  <em>Developed by Rochdi Sabir</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-FastAPI-009688.svg" alt="Made with FastAPI">
  <img src="https://img.shields.io/badge/Powered%20by-SQLAlchemy-red.svg" alt="Powered by SQLAlchemy">
  <img src="https://img.shields.io/badge/Hosted%20on-Docker-2496ED.svg" alt="Hosted on Docker">
</p>
