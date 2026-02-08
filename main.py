"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.config import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database tables
    await init_db()
    yield
    # Shutdown: Cleanup (if needed)


# Create FastAPI application
app = FastAPI(
    title="Todo Web App API - Phase III",
    description="RESTful API for multi-user todo application with JWT authentication and AI chat agent",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Next.js dev server alternative
        "http://localhost:3002",  # Next.js dev server alternative
        "http://127.0.0.1:3000", # Alternative localhost
        "http://127.0.0.1:3001", # Alternative localhost
        "http://127.0.0.1:3002", # Alternative localhost
        "http://192.168.100.26:3002", # Network address
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Todo Web App API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Register routers
from app.routes import auth, todos, chat

app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(todos.router, prefix="/api", tags=["Todos"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])

# Phase III: AI Chat Agent for conversational todo management
