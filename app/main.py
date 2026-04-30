"""FastAPI main application with logging and monitoring"""
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import experiment, assign, event, results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
logger.info("Initializing database...")
Base.metadata.create_all(bind=engine)
logger.info("Database initialized successfully")

# Initialize FastAPI app
app = FastAPI(
    title="Smart A/B Testing Platform",
    description="A/B testing platform with epsilon-greedy bandit algorithm for intelligent variant assignment and statistical significance testing",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Log request processing time and track metrics"""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"[{request_id}] Completed in {process_time:.3f}s with status {response.status_code}")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(experiment.router)
app.include_router(assign.router)
app.include_router(event.router)
app.include_router(results.router)


@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart A/B Testing Platform",
        "version": "1.0.0"
    }


@app.get("/docs", tags=["docs"])
def get_docs():
    """Information about API endpoints"""
    return {
        "message": "Visit /docs for interactive Swagger documentation",
        "endpoints": {
            "POST /experiment": "Create a new A/B test experiment",
            "GET /assign?user_id=X&experiment_id=Y": "Assign user to variant (with ML logic)",
            "POST /event": "Log user event (impression, click, conversion)",
            "GET /results?experiment_id=Y": "Get experiment results and metrics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
