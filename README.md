# LabRats - Secure User Management System

A comprehensive user management system built with FastAPI, PostgreSQL, Redis, and modern web technologies. Features role-based access control, comprehensive security measures, and a beautiful responsive UI.

## 🔥 Features

### Security Features
- ✅ **JWT Authentication** - Secure token-based authentication
- ✅ **Role-based Access Control** - Manager and User roles with appropriate permissions
- ✅ **Password Hashing** - BCrypt with configurable rounds
- ✅ **Rate Limiting** - Prevents brute force attacks and DOS
- ✅ **Account Lockout** - Automatic lockout after failed login attempts
- ✅ **Security Monitoring** - Login attempt logging and analysis
- ✅ **Session Management** - Redis-based caching and session handling
- ✅ **Input Validation** - Comprehensive data validation
- ✅ **CORS Protection** - Configurable cross-origin request handling

### Database Features
- ✅ **PostgreSQL** - Robust relational database
- ✅ **Proper Indexing** - Optimized queries for performance
- ✅ **Migration Support** - Alembic for database versioning
- ✅ **Connection Pooling** - Efficient database connections

### User Interface
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile
- ✅ **Modern UI** - Beautiful glassmorphism design
- ✅ **Real-time Updates** - Dynamic content loading
- ✅ **Toast Notifications** - User-friendly feedback
- ✅ **Loading States** - Smooth user experience

### Management Features
- ✅ **User Registration** - Self-registration with role selection
- ✅ **User Management** - CRUD operations for managers
- ✅ **Profile Management** - Users can update their profiles
- ✅ **Security Dashboard** - Login attempt monitoring
- ✅ **Pagination** - Efficient data browsing
- ✅ **Filtering** - Search and filter capabilities

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** - [Download here](https://python.org)
2. **PostgreSQL 12+** - [Download here](https://postgresql.org)
3. **Redis** - [Download here](https://redis.io)

### Installation (Windows)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AustineIgunza/LabRats.git
   cd LabRats
   ```

2. **Run the setup script:**
   ```bash
   cd backend
   start.bat
   ```
   This script will:
   - Create a virtual environment
   - Install all dependencies
   - Guide you through database setup
   - Start the application

### Manual Installation

1. **Setup Python Environment:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate     # Windows
   # source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   ```bash
   # Copy and edit .env file
   cp .env.example .env
   ```
   
   Update the following variables:
   ```env
   DATABASE_URL=postgresql://labrats_user:labrats_password@localhost:5432/labrats_db
   SECRET_KEY=your-very-long-secret-key-here
   REDIS_URL=redis://localhost:6379
   ```

3. **Setup Database:**
   ```bash
   python setup_db.py
   ```

4. **Start the Application:**
   ```bash
   python main.py
   ```

## 📖 Usage

### Access Points

- **Main Application:** http://localhost:8000
- **API Documentation:** http://localhost:8000/api/docs
- **Alternative API Docs:** http://localhost:8000/api/redoc

### Default Users

After database setup, you'll have these default accounts:

| Role | Email | Password | Access Level |
|------|-------|----------|--------------|
| Manager | admin@labrats.com | admin123 | Full access to user management |
| User | demo@labrats.com | demo123 | Basic user access |

### Testing the Application

#### 1. User Registration
- Go to http://localhost:8000
- Click "Register" tab
- Create a new user account
- Choose role (User or Manager)

#### 2. User Login
- Use any registered credentials
- Access appropriate dashboard based on role

#### 3. Manager Features
- View all users in system
- Edit user information
- Activate/deactivate users
- View security logs
- Monitor login attempts

#### 4. User Features  
- Update personal profile
- View account information

## 🔧 Configuration

### Environment Variables

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database
ASYNC_DATABASE_URL=postgresql+asyncpg://username:password@host:port/database

# Security Configuration
SECRET_KEY=your-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT_PER_MINUTE=5

# Environment
ENVIRONMENT=development  # or production
```

### Security Configuration

#### Rate Limiting
- **API Endpoints:** 60 requests per minute
- **Login Endpoint:** 5 requests per minute
- **Global Rate Limit:** Applied to all requests

#### Account Lockout
- **Max Attempts:** 5 failed login attempts
- **Lockout Duration:** 15 minutes
- **Automatic Reset:** After successful login

#### Password Requirements
- **Minimum Length:** 8 characters
- **Hashing:** BCrypt with 12 rounds
- **Validation:** Server-side validation

## 🏗️ Architecture

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
```

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

## 🔐 Security Implementation

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
1. Redis sliding window algorithm
2. IP-based tracking
3. Different limits for different endpoints
4. Automatic cleanup of old entries

### Security Monitoring
1. All login attempts logged
2. Failed attempts tracked per user
3. IP address monitoring for suspicious activity
4. User agent tracking for analysis

## 🌐 API Endpoints

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

## 📱 Frontend Features

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

## 🚀 Deployment

### Development
```bash
# Start in development mode
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
# Install production server
pip install gunicorn

# Start with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or use uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check PostgreSQL service
net start postgresql-x64-14  # Windows
sudo systemctl start postgresql  # Linux

# Check connection
psql -U labrats_user -d labrats_db -h localhost
```

#### Redis Connection Error
```bash
# Check Redis service
net start redis  # Windows
sudo systemctl start redis  # Linux

# Test connection
redis-cli ping
```

#### Permission Errors
```bash
# Windows: Run as administrator
# Linux: Check file permissions
sudo chmod +x setup_db.py
```

### Performance Optimization

#### Database
- Ensure proper indexing
- Monitor query performance
- Use connection pooling

#### Caching
- Monitor Redis memory usage
- Optimize session data size
- Configure TTL appropriately

#### Rate Limiting
- Adjust limits based on usage
- Monitor blocked requests
- Whitelist trusted IPs if needed

## 📊 Monitoring

### Logs
- Application logs in console
- Database query logs
- Security event logs
- Rate limiting logs

### Metrics to Monitor
- Response times
- Error rates
- Database connections
- Redis memory usage
- Failed login attempts

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Support

For support, please:
1. Check this README
2. Review the API documentation at `/api/docs`
3. Open an issue on GitHub
4. Contact the development team

## 📈 Roadmap

### Upcoming Features
- [ ] Two-factor authentication
- [ ] Email verification
- [ ] Password reset functionality
- [ ] Advanced user permissions
- [ ] Audit logging
- [ ] Dashboard analytics
- [ ] Export functionality
- [ ] Bulk user operations

### Performance Improvements
- [ ] Database query optimization
- [ ] Caching strategies
- [ ] CDN integration
- [ ] Image optimization

---

Built with ❤️ by the LabRats team
