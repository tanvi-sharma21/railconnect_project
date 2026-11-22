# 🚆 RailConnect – Railway Management System

RailConnect is a Python-based Railway Management System built using **FastAPI**. It provides RESTful APIs for user authentication, train management, ticket booking, PNR generation, and booking cancellation.

The project aims to simplify railway reservation operations through a secure and structured backend system.

## ✨ Features

- **User Registration:** Register new users.
- **JWT Authentication:** Secure login using JSON Web Tokens.
- **Admin Authorization:** Restrict train management operations to administrators.
- **Train Management:** Admins can add and manage trains.
- **Train Search:** Search for available trains.
- **Ticket Booking:** Book railway tickets through API endpoints.
- **PNR Generation:** Generate unique PNR numbers for bookings.
- **Booking Management:** View booking details.
- **Ticket Cancellation:** Cancel existing bookings.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API development |
| SQLModel | Database ORM |
| SQLite / PostgreSQL | Database |
| JWT | Authentication |
| Pydantic | Data validation |
| Uvicorn | ASGI server |
| Pytest | Testing |

## 📁 Project Structure

```text
railconnect_project/
│
├── railconnect/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       └── security.py
│
├── tests/
│
 screenshots
├── requirements.txt
└── README.md
```

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2
