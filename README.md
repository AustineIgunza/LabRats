


## Features

### Security Features
-  **JWT Authentication** - Secure token-based authentication
-  **Role-based Access Control** - Manager and User roles with appropriate permissions
-  **Password Hashing** - BCrypt with configurable rounds
-  **Rate Limiting** - Prevents brute force attacks and DOS
-  **Account Lockout** - Automatic lockout after failed login attempts
-  **Security Monitoring** - Login attempt logging and analysis
-  **Session Management** - Redis-based caching and session handling
-  **Input Validation** - Comprehensive data validation
-  **CORS Protection** - Configurable cross-origin request handling

### Database Features
-  **PostgreSQL** - Robust relational database
-  **Proper Indexing** - Optimized queries for performance
-  **Migration Support** - Alembic for database versioning
-  **Connection Pooling** - Efficient database connections

### User Interface
-  **Responsive Design** - Works on desktop, tablet, and mobile
- **Modern UI** - Beautiful glassmorphism design
- **Real-time Updates** - Dynamic content loading
- **Toast Notifications** - User-friendly feedback
- **Loading States** - Smooth user experience

### Management Features
- **User Registration** - Self-registration with role selection
- **User Management** - CRUD operations for managers
- **Profile Management** - Users can update their profiles
- **Security Dashboard** - Login attempt monitoring
- **Pagination** - Efficient data browsing
- **Filtering** - Search and filter capabilities


### Backend Structure
```
backend/
├── main.py              # FastAPI application entry point
├── database.py          # Database models and connection
├── auth.py              # Authentication and authorization
├── models.py            # Pydantic models for API
├── rate_limiter.py      # Rate limiting and DOS protection
├── setup_db.py          # Database setup script
├── requirements.txt     # Python dependencies
├── start.bat           # Windows startup script
└── .env               # Environment configuration

Root Directory:
├── setup_database.py    # Main database setup script
├── start_server.bat    # Quick start script
├── labrats.db          # SQLite database file
└── docker-compose.yml  # Docker configuration (optional)


### Frontend Structure
```
frontend/
├── index.html          # Main HTML template
├── styles.css          # CSS styling (glassmorphism design)
└── app.js             # JavaScript application logic
```

### Database Schema

#### Users Table
- `id` - Primary key
- `email` - Unique email address (indexed)
- `username` - Unique username (indexed)
- `hashed_password` - BCrypt hashed password
- `full_name` - User's full name
- `role` - User role (user/manager) (indexed)
- `is_active` - Account status (indexed)
- `created_at` - Account creation timestamp
- `last_login` - Last successful login
- `failed_login_attempts` - Failed login counter
- `locked_until` - Account lockout expiration

#### Login Attempts Table
- `id` - Primary key
- `email` - Attempted email (indexed)
- `ip_address` - Client IP address (indexed)
- `success` - Login success status (indexed)
- `attempted_at` - Attempt timestamp (indexed)
- `user_agent` - Client browser information

##  Security Implementation

### Authentication Flow
1. User submits credentials
2. Server validates against database
3. JWT token generated with user info and role
4. Token stored in localStorage (client-side)
5. Subsequent requests include Bearer token
6. Server validates token and extracts user context

### Authorization Flow
1. Middleware validates JWT token
2. User role extracted from token
3. Endpoint access checked against role requirements
4. Manager-only endpoints protected by role dependency

### Rate Limiting Implementation
1. In-memory sliding window algorithm using cachetools
2. IP-based tracking
3. Different limits for different endpoints
4. Automatic cleanup of old entries

### Security Monitoring
1. All login attempts logged
2. Failed attempts tracked per user
3. IP address monitoring for suspicious activity
4. User agent tracking for analysis

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### User Management
- `GET /api/users/me` - Get current user info
- `PUT /api/users/me` - Update current user

### Admin Only
- `GET /api/admin/users` - List all users (paginated)
- `PUT /api/admin/users/{id}` - Update any user
- `DELETE /api/admin/users/{id}` - Delete user
- `GET /api/admin/login-attempts` - Security logs

### System
- `GET /api/health` - Health check
- `GET /api/docs` - API documentation

##  Frontend Features

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimized
- Touch-friendly interface

### User Experience
- Loading states for all operations
- Real-time error handling
- Toast notifications for feedback
- Form validation

### Manager Dashboard
- User table with sorting
- Pagination controls
- Search and filtering
- Bulk operations

### Security Features
- Automatic token refresh
- Session timeout handling
- Network error recovery
- Offline detection



