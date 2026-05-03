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
    version="1.2.0",
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
        title="🚀 Smart A/B Testing Platform - Easy A/B Testing with ML",
        description="Production-ready A/B testing with ML-powered variant assignment and statistical significance testing",
        quick_start={
            "step_1_try_demo": "🚀 Try /quick-demo to see complete example (takes 5 seconds!)",
            "step_2_read_guide": "📖 Read /guide/getting-started for step-by-step tutorial",
            "step_3_create_experiment": "📊 POST /experiment with {\"name\": \"my_experiment\"}",
            "step_4_view_results": "📈 GET /results?experiment_id=1 for analysis"
        },
        next_steps=[
            "🚀 NEW: Try /quick-demo to see it in action (instant example!)",
            "📖 NEW: Read /guide/getting-started for interactive tutorial",
            "💡 NEW: Check /metrics-explained to understand the numbers",
            "❓ NEW: Visit /faq for answers to common questions",
            "📊 1️⃣ Create experiment: POST /experiment",
            "🎯 2️⃣ Assign users: GET /assign?user_id=X&experiment_id=Y",
            "📝 3️⃣ Log events: POST /event or /batch-event (bulk upload!)",
            "📈 4️⃣ View results: GET /results?experiment_id=Y"
        ],
        documentation_links={
            "interactive_docs": "/docs (Try API calls live)",
            "quick_demo": "/quick-demo (Auto-running example - 5 seconds!)",
            "getting_started": "/guide/getting-started (Step-by-step tutorial)",
            "metrics_explained": "/metrics-explained (Understand what numbers mean)",
            "faq": "/faq (Answers to common questions)",
            "api_guide": "/api-guide (Complete reference)"
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
        version="1.2.0",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime
    )


@app.get("/quick-demo", tags=["tutorial"])
def quick_demo():
    """
    🚀 QUICK DEMO - See the platform in action instantly!
    Creates an experiment, assigns users, logs events, and shows results.
    Perfect for understanding how everything works together.
    """
    from app.database import SessionLocal
    from app.models import Experiment, Assignment, Event
    
    db = SessionLocal()
    
    # Step 1: Create experiment
    demo_exp = Experiment(name=f"demo_example_{int(time.time())}")
    db.add(demo_exp)
    db.commit()
    db.refresh(demo_exp)
    
    # Step 2: Simulate user assignments and events
    assignments = []
    for user_id in range(1, 11):  # 10 users
        # Assign user
        from app.services.assignment import AssignmentService
        variant, reason = AssignmentService.assign_user(user_id, demo_exp.id, db)
        
        # Log events
        if user_id <= 7:  # 70% see the experiment
            impression = Event(
                user_id=user_id, experiment_id=demo_exp.id, 
                variant=variant, event_type="impression"
            )
            db.add(impression)
            
            if user_id <= 5:  # 50% click
                click = Event(
                    user_id=user_id, experiment_id=demo_exp.id, 
                    variant=variant, event_type="click"
                )
                db.add(click)
                
                if user_id <= 3:  # 30% convert (treatment better!)
                    conversion = Event(
                        user_id=user_id, experiment_id=demo_exp.id, 
                        variant=variant, event_type="conversion"
                    )
                    db.add(conversion)
        
        assignments.append({"user_id": user_id, "variant": variant})
    
    db.commit()
    
    # Step 3: Get results
    from app.services.metrics import MetricsCalculator
    results = MetricsCalculator.get_experiment_metrics(demo_exp.id, db)
    
    db.close()
    
    return {
        "title": "✨ Quick Demo - Complete Example",
        "what_happened": "Created experiment, assigned 10 users, logged events, analyzed results",
        "experiment": {
            "id": demo_exp.id,
            "name": demo_exp.name,
            "status": "completed"
        },
        "user_assignments": {
            "total_users": len(assignments),
            "sample_distribution": {"control": sum(1 for a in assignments if a['variant'] == 'control'),
                                    "treatment": sum(1 for a in assignments if a['variant'] == 'treatment')}
        },
        "results_summary": {
            "control": f"CR: {results['control']['conversion_rate']:.1%}",
            "treatment": f"CR: {results['treatment']['conversion_rate']:.1%}",
            "winner": "🎉 Treatment is significantly better!" if results['is_significant'] else "Need more data",
            "confidence": f"P-Value: {results['p_value']:.4f} (< 0.05 = significant)",
            "uplift": f"{results['uplift']:+.1%}"
        },
        "next_steps": [
            "✅ This is how the platform works!",
            "📖 Read /guide/getting-started to create your own experiment",
            "💡 Check /metrics-explained to understand the metrics",
            "🎯 Create your real experiment: POST /experiment"
        ]
    }


@app.get("/guide/getting-started", tags=["tutorial"])
def getting_started_guide():
    """
    📖 INTERACTIVE GUIDE - Learn step-by-step how to use the platform!
    """
    return {
        "title": "📖 Getting Started Guide",
        "estimated_time": "5 minutes",
        "steps": [
            {
                "step": 1,
                "title": "✨ See It In Action (1 min)",
                "description": "Visit /quick-demo to see a complete example running",
                "action": "GET /quick-demo",
                "what_you_learn": "How the full workflow works"
            },
            {
                "step": 2,
                "title": "📊 Create Your First Experiment (1 min)",
                "description": "Create an experiment with a unique name",
                "action": 'POST /experiment with {"name": "my_first_test"}',
                "what_you_learn": "How to initialize experiments"
            },
            {
                "step": 3,
                "title": "🎯 Assign Your First User (1 min)",
                "description": "The ML algorithm will assign them randomly (exploration phase)",
                "action": "GET /assign?user_id=1&experiment_id=YOUR_EXP_ID",
                "what_you_learn": "How ML assignment works"
            },
            {
                "step": 4,
                "title": "📝 Log User Events (1 min)",
                "description": "Track when they see, click, or convert on something",
                "action": 'POST /event with {"user_id": 1, "experiment_id": ID, "variant": "control", "event_type": "impression"}',
                "what_you_learn": "How to track user behavior"
            },
            {
                "step": 5,
                "title": "📈 View Results (1 min)",
                "description": "See statistics and check if results are significant",
                "action": "GET /results?experiment_id=YOUR_EXP_ID",
                "what_you_learn": "How statistical testing works"
            }
        ],
        "quick_reference": {
            "create_experiment": 'POST /experiment → {"name": "test_name"}',
            "assign_user": "GET /assign?user_id=123&experiment_id=1",
            "log_event": 'POST /event → {"user_id": 123, "experiment_id": 1, "variant": "control", "event_type": "impression"}',
            "batch_events": 'POST /batch-event → [{"user_id": 123, ...}, {...}]',
            "get_results": "GET /results?experiment_id=1",
            "check_status": "GET /experiment/1/status"
        },
        "helpful_links": {
            "metrics_explained": "/metrics-explained (Understand CTR, conversion rate, etc)",
            "faq": "/faq (Common questions answered)",
            "api_guide": "/api-guide (Complete API reference)"
        }
    }


@app.get("/metrics-explained", tags=["learning"])
def metrics_explained():
    """
    📊 METRICS GUIDE - Understand what each number means!
    """
    return {
        "title": "📊 Understanding Your Metrics",
        "subtitle": "A beginner-friendly guide to A/B testing statistics",
        "metrics": {
            "impressions": {
                "what_it_is": "Number of times a variant was shown to users",
                "why_it_matters": "More impressions = more reliable data",
                "example": "If you show 1000 users the control variant, impressions = 1000"
            },
            "clicks": {
                "what_it_is": "Number of users who clicked on something",
                "why_it_matters": "Shows if the variant is interesting",
                "example": "100 clicks out of 1000 impressions"
            },
            "conversions": {
                "what_it_is": "Number of users who completed the goal (purchase, signup, etc)",
                "why_it_matters": "Most important metric - shows if variant actually works",
                "example": "20 conversions out of 1000 impressions = 2% conversion"
            },
            "CTR": {
                "full_name": "Click-Through Rate",
                "what_it_is": "Percentage of people who clicked (clicks / impressions)",
                "formula": "CTR = clicks / impressions",
                "example": "100 clicks / 1000 impressions = 10% CTR",
                "interpretation": "Higher CTR = more engaging"
            },
            "conversion_rate": {
                "what_it_is": "Percentage of people who converted (conversions / impressions)",
                "formula": "Conversion Rate = conversions / impressions",
                "example": "20 conversions / 1000 impressions = 2% conversion rate",
                "interpretation": "Higher = better"
            },
            "uplift": {
                "what_it_is": "How much better treatment is than control",
                "formula": "Uplift = (treatment - control) / control",
                "example": "Control 2%, Treatment 2.5% → Uplift = +25%",
                "interpretation": "Positive = treatment wins, negative = control wins"
            },
            "p_value": {
                "what_it_is": "Confidence that results didn't happen by chance",
                "rule_of_thumb": "p < 0.05 = significant (95% confident)",
                "example": "p_value = 0.03 means 97% confident difference is real",
                "interpretation": "Lower = more confident in results"
            },
            "z_score": {
                "what_it_is": "Statistical strength of the difference",
                "interpretation": "|z| > 1.96 usually means significant",
                "example": "z = 2.5 means fairly strong difference"
            },
            "is_significant": {
                "what_it_is": "YES/NO - Can we trust these results?",
                "when_true": "When p_value < 0.05 (95% confidence)",
                "when_false": "Need more data, differences might be chance",
                "action": "Only make decisions when is_significant = true!"
            }
        },
        "decision_rules": {
            "rule_1": "🔴 Need more data: impressions < 100 per variant",
            "rule_2": "🟡 Maybe useful: impressions 100-1000, significance unclear",
            "rule_3": "🟢 Trust it: impressions > 1000 AND is_significant = true",
            "rule_4": "⚡ Always check: is_significant=true before making decisions"
        },
        "common_scenarios": {
            "scenario_1": {
                "situation": "High uplift (50%) but p_value = 0.20",
                "why": "Might be lucky - not enough data",
                "what_to_do": "Run longer, log more events"
            },
            "scenario_2": {
                "situation": "Low uplift (5%) but p_value = 0.001",
                "why": "Consistent small difference across many users",
                "what_to_do": "Decision depends on business value of 5% improvement"
            },
            "scenario_3": {
                "situation": "No uplift (0%) and p_value = 0.95",
                "why": "Variants perform identically",
                "what_to_do": "Try a different variant, they're equally good"
            }
        }
    }


@app.get("/faq", tags=["learning"])
def faq():
    """
    ❓ FAQ - Answers to common questions!
    """
    return {
        "title": "❓ Frequently Asked Questions",
        "faqs": [
            {
                "question": "How do I get started?",
                "answer": "Visit /guide/getting-started or try /quick-demo first!"
            },
            {
                "question": "What's the difference between control and treatment?",
                "answer": "Control = current experience, Treatment = new idea you're testing"
            },
            {
                "question": "How many users do I need to run an experiment?",
                "answer": "Aim for 100+ impressions per variant minimum, 1000+ for reliable results"
            },
            {
                "question": "What does p_value mean?",
                "answer": "Confidence that results didn't happen by chance. p < 0.05 = 95% confident"
            },
            {
                "question": "When can I make a decision?",
                "answer": "When is_significant = true AND you have enough data (1000+ impressions)"
            },
            {
                "question": "Can I use the same user in multiple experiments?",
                "answer": "Yes! Each experiment is independent. One user can be in many tests."
            },
            {
                "question": "What's the ML algorithm doing?",
                "answer": "Epsilon-greedy: 10% random exploration, 90% pick the winner"
            },
            {
                "question": "How do I log multiple events quickly?",
                "answer": "Use POST /batch-event to log many events at once!"
            },
            {
                "question": "What if both variants perform the same?",
                "answer": "Great! Pick the easier/cheaper one to maintain"
            },
            {
                "question": "Can I run multiple experiments on the same users?",
                "answer": "Yes! They're independent. Good for testing different changes"
            }
        ]
    }


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
