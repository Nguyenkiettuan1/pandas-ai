from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.core.database import engine
from app.core.logging_config import setup_logging, get_logger
from app.routes import dataset_router, query_router, conversation_router
from app.models import Base

# Setup logging first
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up PandasAI Q&A System...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Create database tables (optional for demo)
    if not settings.SKIP_DB_INIT:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.warning(f"Failed to create database tables (running without DB): {e}")
            logger.info("Application will run with limited functionality (response handler demo only)")
    else:
        logger.info("Skipping database initialization (SKIP_DB_INIT=True)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PandasAI Q&A System...")

app = FastAPI(
    title="PandasAI Q&A System",
    description="Natural Language Q&A System using PandasAI and FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dataset_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to PandasAI Q&A System", "status": "running"}

@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy", "timestamp": "2025-06-11"}

@app.get("/api/v1/profiles")
async def list_agent_profiles():
    """List available agent profiles"""
    logger.info("Listing agent profiles")
    from app.agents.profile_manager import profile_manager
    
    profiles_info = []
    for profile_name in profile_manager.list_profiles():
        profile_info = profile_manager.get_profile_info(profile_name)
        if profile_info:
            profiles_info.append(profile_info)
    
    return {"profiles": profiles_info}

@app.get("/api/v1/tools")
async def list_available_tools():
    """List available analysis tools"""
    logger.info("Listing available tools")
    from app.agents.pandas_agent import PandasAIAgent
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        agent = PandasAIAgent(db)
        tools = agent.list_available_tools()
        return {"tools": tools}
    finally:
        db.close()

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
