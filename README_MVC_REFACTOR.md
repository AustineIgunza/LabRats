# LabRats Project - MVC Refactoring Complete ✅

## Summary
Your LabRats user management system has been successfully refactored from a monolithic FastAPI structure into a clean MVC (Model-View-Controller) architecture.

---

## What Changed

### Backend Structure
**Before:** All routes in `backend/main.py`  
**After:** Routes organized by feature in `backend/controllers/`:
- `auth_controller.py` — Register, Login, Logout
- `user_controller.py` — Profile management (current user)
- `admin_controller.py` — User list, edit, delete, security logs (manager only)

**Models & Services (unchanged):**
- `database.py` — SQLAlchemy ORM models (User, LoginAttempt)
- `models.py` — Pydantic schemas (request/response)
- `auth.py` — AuthService (authentication, tokens, caching)
- `rate_limiter.py` — Rate limiting, DoS protection, IP blocking
- `main.py` — App initialization, middleware, router registration

---

## How It Works

### Register → Login → Dashboard Flow
1. **POST /api/auth/register** (Public)
   - Creates user with hashed password
   - Returns UserResponse with id, role, etc.

2. **POST /api/auth/login** (Public)
   - Authenticates with email + password
   - Returns JWT access_token + user + expires_in
   - Caches user session in-memory (30 min TTL)

3. **GET/PUT /api/users/me** (Protected, any role)
   - Requires Bearer token
   - Returns/updates current user profile

4. **GET /api/admin/users, PUT/DELETE /api/admin/users/{id}** (Protected, manager only)
   - Paginated user list with filters
   - Edit user role/status
   - Delete user (not self)

5. **GET /api/admin/login-attempts** (Protected, manager only)
   - Security logs with filters (email, success, time range)

### Frontend (Single-Page App)
- **Auth**: Register/Login forms with localStorage token persistence
- **User Dashboard**: Profile settings
- **Manager Dashboard**: User management, security logs, filters, pagination
- Modern UI with toast notifications, loading states, role-based sections

---

## Technology Stack
- **Backend**: FastAPI, SQLAlchemy (SQLite by default), Pydantic, python-jose (JWT), passlib (bcrypt)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3, Font Awesome icons
- **Security**: JWT tokens, bcrypt password hashing, rate limiting, DoS protection, account lockout

---

## Running Locally

### Prerequisites
- Python 3.12+
- Dependencies (included in `backend/requirements.txt`)

### Start the Server
```powershell
C:/Users/mmatt/AppData/Local/Microsoft/WindowsApps/python3.12.exe -m uvicorn backend.main:app --reload
```

Server runs at **http://127.0.0.1:8000**

### Use the App
1. Open http://127.0.0.1:8000/ in browser
2. **Register**: new email, username (3+ chars), full name, password (8+ chars), role
3. **Login**: use registered email + password → navigate to dashboard
4. **Manage** (as manager): edit/delete users, view login attempts

### API Testing (curl/Postman)
```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"you@example.com",
    "username":"you",
    "full_name":"Your Name",
    "password":"Password123!",
    "role":"user"
  }'

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Password123!"}'

# Protected: Get current user (replace TOKEN with access_token from login)
curl -X GET http://127.0.0.1:8000/api/users/me \
  -H "Authorization: Bearer TOKEN"
```

---

## Features

### Security
- ✅ Password hashing (bcrypt)
- ✅ JWT authentication (30 min expiry, configurable)
- ✅ Rate limiting (60 req/min default, 5 attempts for login)
- ✅ DoS protection (100 req/min threshold, 15 min IP block)
- ✅ Account lockout (5 failed attempts → 15 min lock)
- ✅ Login attempt logging (email, IP, user-agent, success/fail)
- ✅ Session caching (in-memory, 30 min TTL)

### User Management
- ✅ Register (role-based: user/manager)
- ✅ Login with token generation
- ✅ Profile update (self)
- ✅ List users with pagination & filters (role, active status)
- ✅ Edit user (manager only)
- ✅ Delete user (manager only, not self)

### Monitoring
- ✅ Security logs (login attempts, IP blocking events)
- ✅ Filters: email, success/fail, time range (1h/24h/1w/1m)

---

## Database

**Default**: SQLite (`labrats.db` in project root)  
**Tables**:
- `users` — id, email, username, hashed_password, full_name, role, is_active, created_at, last_login, failed_login_attempts, locked_until
- `login_attempts` — id, email, ip_address, success, attempted_at, user_agent

**Environment Variable** (optional):
```
DATABASE_URL=postgresql://user:password@localhost/labrats
```

---

## Troubleshooting

### "Incorrect email or password" when login is correct
- **Account locked**: Caused by 5+ failed attempts (15 min lockout). Wait or reset in DB.
- **DB sync issue**: Ensure frontend and backend use same database.
- **Check server logs**: Look for [DEBUG] or error messages.

### "Email or username already registered"
- User exists in DB. Try different email/username or clear DB: `rm labrats.db`

### Rate limit (429 Too Many Requests)
- Made 60+ requests in 60 seconds. Wait or restart server.

### CORS errors
- Frontend calls wrong origin. Verify request URL in browser DevTools → Network tab.
- Update `allow_origins` in `backend/main.py` if serving from different port/host.

---

## Project Structure
```
backend/
  ├── controllers/
  │   ├── __init__.py
  │   ├── auth_controller.py       (register, login, logout)
  │   ├── user_controller.py       (profile)
  │   └── admin_controller.py      (user management, logs)
  ├── auth.py                       (AuthService, dependencies)
  ├── database.py                   (models, session)
  ├── main.py                       (app, middleware, startup)
  ├── models.py                     (Pydantic schemas)
  ├── rate_limiter.py              (rate limiting, DoS, IP blocking)
  ├── requirements.txt
  └── scripts/
      └── test_auth.py             (smoke test)

frontend/
  ├── index.html                   (UI)
  ├── app.js                       (logic, API calls)
  └── styles.css                   (styling)
```

---

## Next Steps (Optional Enhancements)

- [ ] Add pytest unit tests for controllers + services
- [ ] Add email verification for registration
- [ ] Add password reset flow
- [ ] Add 2FA (TOTP)
- [ ] Migrate to PostgreSQL for production
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Deploy to cloud (Heroku, AWS, DigitalOcean, etc.)
- [ ] Add API documentation (Swagger at /api/docs already included)

---

## Contact / Support
If issues arise, check:
1. Browser DevTools → Network tab for API response details
2. Terminal logs for stack traces
3. Database state (inspect `labrats.db` with sqlite3)
4. Environment variables (SECRET_KEY, DATABASE_URL, rate limits)

---

**Status**: ✅ Fully functional MVC refactoring complete. Ready for testing and deployment.
