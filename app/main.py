"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import experiment, assign, event, results

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Smart A/B Testing Platform",
    description="A/B testing platform with epsilon-greedy bandit algorithm for intelligent variant assignment",
    version="1.0.0"
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
