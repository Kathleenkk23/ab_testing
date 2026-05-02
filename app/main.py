"""FastAPI main application with logging and monitoring"""
import logging
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Initialize FastAPI app with enhanced metadata
app = FastAPI(
    title="Smart A/B Testing Platform",
    description="Production-ready A/B testing platform with epsilon-greedy bandit algorithm for intelligent variant assignment and statistical significance testing (two-proportion z-test)",
    version="1.1.0",
    contact={
        "name": "API Support",
        "description": "Complete A/B testing solution for data-driven decision making",
    },
    license_info={
        "name": "MIT License",
    },
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


# Response models for better UX
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str
    uptime_seconds: float


class WelcomeResponse(BaseModel):
    """Welcome and quick start guide"""
    title: str
    description: str
    quick_start: dict
    next_steps: list
    documentation_links: dict


class EndpointInfo(BaseModel):
    """Detailed endpoint information"""
    method: str
    path: str
    description: str
    parameters: dict
    example_request: dict
    example_response: dict


# Track app startup time
app_start_time = time.time()


@app.get("/", tags=["welcome"], response_model=WelcomeResponse)
def welcome():
    """
    Welcome endpoint with quick start guide and API overview.
    Start here to learn how to use the platform!
    """
    return WelcomeResponse(
        title="🚀 Smart A/B Testing Platform",
        description="Production-ready A/B testing with ML-powered variant assignment and statistical significance testing",
        quick_start={
            "step_1_create_experiment": "POST /experiment with {\"name\": \"my_experiment\"}",
            "step_2_assign_users": "GET /assign?user_id=1&experiment_id=1",
            "step_3_log_events": "POST /event with {\"user_id\": 1, \"experiment_id\": 1, \"variant\": \"control\", \"event_type\": \"impression\"}",
            "step_4_get_results": "GET /results?experiment_id=1"
        },
        next_steps=[
            "1️⃣ Create an experiment: POST /experiment",
            "2️⃣ Assign users: GET /assign?user_id=X&experiment_id=Y",
            "3️⃣ Log user events (impressions, clicks, conversions): POST /event",
            "4️⃣ Analyze results with statistical significance: GET /results?experiment_id=Y"
        ],
        documentation_links={
            "interactive_docs": "/docs (Swagger UI - try API calls here)",
            "alternative_docs": "/redoc (ReDoc - read-only documentation)",
            "health_status": "/health (API health check)",
            "github_repo": "https://github.com/YOUR_USERNAME/ab_testing"
        }
    )


@app.get("/health", tags=["health"], response_model=HealthResponse)
def health_check():
    """
    Health check endpoint with detailed status information.
    Use this to verify the API is running and responsive.
    """
    uptime = time.time() - app_start_time
    return HealthResponse(
        status="healthy ✅",
        service="Smart A/B Testing Platform",
        version="1.1.0",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime
    )


@app.get("/api-guide", tags=["documentation"])
def api_guide():
    """
    Comprehensive API guide with examples and best practices.
    """
    return {
        "title": "A/B Testing Platform - API Guide",
        "base_url": "http://localhost:8000",
        "authentication": "None required (open API)",
        "endpoints": {
            "experiments": {
                "create": {
                    "method": "POST",
                    "path": "/experiment",
                    "description": "Create a new A/B test experiment",
                    "example_request": {"name": "homepage_button_color_v1"},
                    "example_response": {
                        "id": 1,
                        "name": "homepage_button_color_v1",
                        "status": "active",
                        "created_at": "2026-05-02T10:00:00",
                        "next_steps": "Ready to assign users! Use GET /assign?user_id=1&experiment_id=1 to start"
                    }
                },
                "get": {
                    "method": "GET",
                    "path": "/experiment/{experiment_id}",
                    "description": "Get experiment details",
                    "example_request": "GET /experiment/1",
                    "example_response": {
                        "id": 1,
                        "name": "homepage_button_color_v1",
                        "status": "active"
                    }
                }
            },
            "assignment": {
                "assign_user": {
                    "method": "GET",
                    "path": "/assign",
                    "description": "Assign user to control or treatment variant using ML algorithm",
                    "parameters": {
                        "user_id": "Unique user identifier (integer > 0)",
                        "experiment_id": "Experiment ID (integer > 0)"
                    },
                    "algorithm": "Epsilon-greedy bandit (90% exploit best, 10% explore)",
                    "example_request": "GET /assign?user_id=123&experiment_id=1",
                    "example_response": {
                        "user_id": 123,
                        "experiment_id": 1,
                        "variant": "treatment",
                        "assignment_reason": "Exploitation phase (exploit): assigned best: treatment",
                        "next_steps": "Log events for this user: POST /event with user_id=123, experiment_id=1, variant='treatment'"
                    }
                }
            },
            "events": {
                "log_event": {
                    "method": "POST",
                    "path": "/event",
                    "description": "Log user event (impression, click, conversion)",
                    "event_types": ["impression", "click", "conversion"],
                    "variants": ["control", "treatment"],
                    "example_request": {
                        "user_id": 123,
                        "experiment_id": 1,
                        "variant": "treatment",
                        "event_type": "click"
                    },
                    "example_response": {
                        "id": 1,
                        "user_id": 123,
                        "experiment_id": 1,
                        "variant": "treatment",
                        "event_type": "click"
                    }
                }
            },
            "results": {
                "get_results": {
                    "method": "GET",
                    "path": "/results",
                    "description": "Get experiment results with statistical significance testing",
                    "parameters": {
                        "experiment_id": "Experiment ID (integer > 0)"
                    },
                    "example_request": "GET /results?experiment_id=1",
                    "metrics_returned": {
                        "impressions": "Total times variant was shown",
                        "clicks": "Total clicks on variant",
                        "conversions": "Total conversions for variant",
                        "ctr": "Click-through rate (clicks / impressions)",
                        "conversion_rate": "Conversion rate (conversions / impressions)"
                    },
                    "statistical_metrics": {
                        "uplift": "Relative improvement (treatment - control)",
                        "z_score": "Z-statistic from two-proportion z-test",
                        "p_value": "Statistical significance (two-tailed)",
                        "is_significant": "Is the result statistically significant at 95% confidence?"
                    }
                }
            }
        },
        "best_practices": {
            "sample_size": "Aim for 100+ impressions per variant before making decisions",
            "event_logging": "Always log 'impression' event first, then 'click', then 'conversion'",
            "statistical_significance": "Only trust results when is_significant=true (p_value < 0.05)",
            "experiment_naming": "Use descriptive names: 'feature_x_vs_control', 'layout_test_v2'",
            "monitoring": "Check results daily to ensure variant quality"
        },
        "error_codes": {
            "400": "Bad request - invalid input (check field constraints)",
            "404": "Not found - experiment or resource doesn't exist",
            "422": "Unprocessable entity - validation failed (check field formats)",
            "500": "Server error - unexpected issue (check logs)"
        },
        "tips": {
            "tip_1": "Use X-Request-ID header to track specific requests in logs",
            "tip_2": "Response includes X-Process-Time header for performance monitoring",
            "tip_3": "All timestamps are in ISO 8601 format (UTC)",
            "tip_4": "API is stateless - requests can be replayed safely"
        }
    }


@app.get("/docs", tags=["documentation"])
def get_docs():
    """
    Documentation overview with links to interactive tools.
    """
    return {
        "message": "Welcome! Choose your preferred documentation format:",
        "interactive_swagger_ui": "/docs - Try API calls here with auto-completion",
        "static_redoc": "/redoc - Clean, read-only documentation",
        "api_guide": "/api-guide - Complete guide with examples",
        "quick_start": "/",
        "health_check": "/health",
        "note": "All endpoints are fully documented inline. Hover over fields for descriptions."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
