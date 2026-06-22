# 💬 ChatShare — File Sharing & Real-Time Chat Application

A production-ready full-stack application built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Alembic**, **JWT Authentication**, **WebSockets**, and **Streamlit**.

---

## 🏗️ Architecture

```
ChatApp/
├── backend/           # FastAPI REST API + WebSocket server
│   ├── app/
│   │   ├── api/       # Route handlers (v1)
│   │   ├── core/      # Config, security, exceptions
│   │   ├── database/  # SQLAlchemy engine & session
│   │   ├── models/    # ORM models (6 tables)
│   │   ├── schemas/   # Pydantic request/response models
│   │   ├── services/  # Business logic layer
│   │   ├── repositories/ # Database query layer
│   │   ├── websocket/ # ConnectionManager + handlers
│   │   ├── dependencies/ # FastAPI dependencies
│   │   └── main.py    # Application entry point
│   ├── alembic/       # Database migrations
│   ├── tests/         # Pytest test suite
│   └── uploads/       # Local file storage
├── frontend/          # Streamlit UI
│   ├── pages/         # Multi-page Streamlit app
│   ├── components/    # Reusable UI components
│   ├── services/      # API & WebSocket clients
│   ├── utils/         # Helper utilities
│   └── app.py         # Entry point (Login/Register)
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16+ (installed locally)

### 1. Set Up PostgreSQL

Create a database and user:

```sql
-- Connect to PostgreSQL as superuser (psql -U postgres)
CREATE USER chatshare WITH PASSWORD 'chatshare_secret';
CREATE DATABASE chatshare_db OWNER chatshare;
GRANT ALL PRIVILEGES ON DATABASE chatshare_db TO chatshare;
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate venv
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env if your PostgreSQL credentials differ

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 3. Frontend Setup

Open a **new terminal**:

```bash
cd frontend

# Create virtual environment
python -m venv .venv

# Activate venv
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Streamlit
streamlit run app.py
```

Frontend will be available at: **http://localhost:8501**

---

## 📋 Features

### Authentication & Authorization
- ✅ User Registration with validation
- ✅ JWT-based Login (access + refresh tokens)
- ✅ Token refresh & logout with blacklisting
- ✅ Password hashing (bcrypt)
- ✅ Protected API endpoints
- ✅ Profile management & password change

### Room Management
- ✅ Create, update, delete rooms
- ✅ Public & private rooms
- ✅ Search rooms with pagination
- ✅ Join requests for private rooms
- ✅ Approve/reject join requests
- ✅ Role-based access (Creator → Admin → Member)
- ✅ Promote/demote members
- ✅ Remove members

### Real-Time Chat
- ✅ WebSocket-based messaging
- ✅ Room-specific communication
- ✅ Message history with cursor-based pagination
- ✅ Typing indicators
- ✅ Read receipts
- ✅ Online/offline status tracking
- ✅ Auto-reconnection support

### File Sharing
- ✅ Upload files (PDF, DOCX, XLSX, TXT, Images, ZIP)
- ✅ Download files
- ✅ Delete files (uploader/admin/creator)
- ✅ File type & size validation
- ✅ Access restricted to room members
- ✅ Abstract storage backend (ready for S3/MinIO migration)

### Security
- ✅ JWT Authentication
- ✅ Password hashing (bcrypt)
- ✅ Input validation (Pydantic)
- ✅ File type validation (allowlist)
- ✅ File size limits (configurable)
- ✅ Rate limiting (slowapi)
- ✅ CORS configuration
- ✅ SQL injection protection (parameterized queries)

---

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `users` | User accounts with hashed passwords |
| `rooms` | Chat rooms (public/private) |
| `room_members` | Room membership with roles |
| `join_requests` | Pending access requests |
| `messages` | Chat message history |
| `files` | Uploaded file metadata |

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login & get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Invalidate token |
| GET | `/api/v1/auth/me` | Get current user |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get profile |
| PUT | `/api/v1/users/me` | Update profile |
| PUT | `/api/v1/users/me/password` | Change password |

### Rooms
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/rooms` | Create room |
| GET | `/api/v1/rooms` | List rooms |
| GET | `/api/v1/rooms/{id}` | Get room detail |
| PUT | `/api/v1/rooms/{id}` | Update room |
| DELETE | `/api/v1/rooms/{id}` | Delete room |
| POST | `/api/v1/rooms/{id}/join` | Join/request access |
| POST | `/api/v1/rooms/{id}/leave` | Leave room |
| GET | `/api/v1/rooms/{id}/members` | List members |
| DELETE | `/api/v1/rooms/{id}/members/{uid}` | Remove member |
| PUT | `/api/v1/rooms/{id}/members/{uid}/role` | Change role |
| GET | `/api/v1/rooms/{id}/requests` | List join requests |
| PUT | `/api/v1/rooms/{id}/requests/{rid}` | Handle request |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/rooms/{id}/messages` | Get message history |
| WS | `/ws/{room_id}?token=...` | WebSocket connection |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/rooms/{id}/files` | Upload file |
| GET | `/api/v1/rooms/{id}/files` | List files |
| GET | `/api/v1/rooms/{id}/files/{fid}/download` | Download file |
| DELETE | `/api/v1/rooms/{id}/files/{fid}` | Delete file |

---

## 🧪 Testing

```bash
cd backend

# Activate venv
.\.venv\Scripts\activate

# Run all tests
pytest tests/ -v --asyncio-mode=auto

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## ⚙️ Environment Variables

Edit `backend/.env` to configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://chatshare:chatshare_secret@localhost:5432/chatshare_db` | Database connection |
| `SECRET_KEY` | — | JWT signing secret (change in production!) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `UPLOAD_DIR` | `uploads` | File storage directory |
| `MAX_FILE_SIZE_MB` | `50` | Max upload size |
| `ALLOWED_EXTENSIONS` | `.pdf,.docx,.xlsx,.txt,.png,.jpg,.jpeg,.gif,.zip` | Allowed file types |
| `CORS_ORIGINS` | `http://localhost:8501` | Allowed origins |
| `DEBUG` | `true` | Enable debug mode |

---

## 📄 License

This project is licensed under the terms specified in the LICENSE file.
