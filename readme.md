# User Management System

This repository contains the **User Management System** developed as part of the Software QA Analyst/Developer onboarding project for Prof. Keith Williams' class at NJIT.

## Project Overview

The User Management System provides a secure and reliable way to manage user accounts, including profile management, authentication, role-based access control, and email notifications.

## Features Implemented

* **User Registration and Authentication:** Secure registration, login, and JWT-based authentication.
* **User Profile Management:** Users can update their profile details, including a new "Display Name" feature.
* **Professional User Promotion:** Administrators can promote users to a professional status, triggering automated email notifications.
* **Role-Based Access Control:** Fine-grained permissions for various user roles (ADMIN, MANAGER, AUTHENTICATED, ANONYMOUS).
* **Automated Email Notifications:** Integrated email services for verification and professional status notifications.

## Technology Stack

* **Backend:** Python, FastAPI
* **Database:** PostgreSQL, SQLAlchemy, Alembic
* **Email Service:** SMTP with Mailtrap for testing
* **Storage:** MinIO (object storage for profile pictures)
* **Containerization:** Docker
* **CI/CD:** GitHub Actions, DockerHub

## Installation

### Prerequisites

* Docker and Docker Compose installed.
* GitHub CLI (optional for quick setup).

### Quick Setup

Clone repository:

```bash
git clone https://github.com/yeomigie/user_management_final_proj.git
cd user_management_final_proj
```

Start the application using Docker Compose:

```bash
docker-compose up --build
```

The application will run at: `http://localhost:8000`

## API Documentation

Interactive API documentation available via Swagger UI:

```
http://localhost:8000/docs
```

## Running Tests

To run automated tests locally:

```bash
docker-compose exec web pytest
```

## CI/CD and Deployment

* GitHub Actions workflow ensures automatic testing, Docker image building, and vulnerability scanning.
* Deployed Docker image on DockerHub: [yeomigie098/user_management_final_proj/user-management](https://hub.docker.com/repository/docker/yeomigie098/user_management_final_proj)

![CI Status](https://github.com/yeomigie/user_management_final_proj/actions/workflows/main.yml/badge.svg)

## Resolved Issues

* [#2 Profile Picture URL Validation](https://github.com/Sarachaker/user_management_final_proj/issues/2)
* [#3 Missing Nickname Auto-Generation](https://github.com/Sarachaker/user_management_final_proj/issues/3)
* [#4 Docker Build Failure](https://github.com/Sarachaker/user_management_final_proj/issues/4)
* [#5 DockerHub Vulnerabilities](https://github.com/Sarachaker/user_management_final_proj/issues/5)
* [#6 Email Verification Restrictions](https://github.com/Sarachaker/user_management_final_proj/issues/6)
* [#7 Comprehensive API Tests](https://github.com/Sarachaker/user_management_final_proj/issues/7)

## Screenshots

| Screenshot                                         | Description                                                                               |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| ![Swagger UI](docs/images/swagger_ui.png)          | Interactive API docs demonstrating the new **display\_name** field in the profile schema. |
| ![Pytest Coverage](docs/images/pytest_results.png) | Successful test run showing >90 % coverage across the user‑management endpoints.          |
| ![GitHub Actions](docs/images/ci_pipeline.png)     | Green CI pipeline confirming migrations, tests, and Docker image push.                    |
| ![DockerHub](docs/images/dockerhub_repo.png)       | DockerHub repository page with the latest image tag and pull stats.                       |

> **Tip:** Capture these images locally (or via GitHub UI) and place them under `docs/images/`; the Markdown paths above assume that structure.

---

## Project Structure

```
.
├── app
│   ├── models
│   ├── routers
│   ├── schemas
│   ├── services
│   └── utils
├── tests
│   ├── conftest.py
│   └── test_user_api.py
├── alembic (database migrations)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Future Enhancements

* Profile picture versioning
* Advanced role management
* Performance benchmarking