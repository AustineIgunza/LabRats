from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="LabRats Management System",
    description="A secure user management system with role-based access control",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Use rate_limiter instance as a simple http middleware
from .rate_limiter import rate_limiter
from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if await rate_limiter.is_ip_blocked(request):
        return JSONResponse(
            status_code=423,
            content={"detail": "Your IP has been temporarily blocked due to suspicious activity"}
        )
    return await call_next(request)

# Mount static files (for frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Register routers (controllers)
from .controllers import auth_controller, user_controller, admin_controller
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(admin_controller.router)

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    from .database import create_tables
    create_tables()

# Root endpoint - serve the frontend
@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>LabRats API Server</h1><p>Frontend files not found. API documentation: <a href='/api/docs'>/api/docs</a></p>",
            status_code=200
        )

# Health check
@app.get("/api/health")
async def health_check():
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"]
    )
