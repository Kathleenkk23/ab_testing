"""FastAPI main application with logging and monitoring"""
import logging
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.database import engine, Base, create_indexes, optimize_database
from app.routes import experiment, assign, event, results, templates, creative

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

# Create performance indexes
logger.info("Creating database indexes...")
if create_indexes():
    logger.info("Database indexes created successfully")
else:
    logger.warning("Some database indexes may not have been created")

# Optimize database
logger.info("Optimizing database...")
if optimize_database():
    logger.info("Database optimization completed")
else:
    logger.warning("Database optimization may not have completed successfully")

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
app.include_router(templates.router)
app.include_router(creative.router)


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


@app.get("/", tags=["welcome"], response_class=HTMLResponse)
def welcome():
    """
    Enhanced welcome page with better UX and clear value proposition.
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Smart A/B Testing Platform</title>
      <style>
        * { box-sizing: border-box; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
          margin: 0;
          padding: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: #1a202c;
          line-height: 1.6;
        }
        .hero {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 80px 24px 60px;
          text-align: center;
        }
        .hero h1 {
          font-size: 3.5rem;
          font-weight: 800;
          margin: 0 0 16px;
          text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .hero p {
          font-size: 1.25rem;
          margin: 0 0 32px;
          opacity: 0.9;
          max-width: 600px;
          margin-left: auto;
          margin-right: auto;
        }
        .hero .cta {
          display: inline-block;
          background: #48bb78;
          color: white;
          padding: 16px 32px;
          border-radius: 12px;
          text-decoration: none;
          font-weight: 600;
          font-size: 1.1rem;
          transition: all 0.2s;
          box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
        }
        .hero .cta:hover {
          background: #38a169;
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(72, 187, 120, 0.4);
        }
        .container {
          max-width: 1200px;
          margin: -40px auto 0;
          background: white;
          border-radius: 24px 24px 0 0;
          padding: 60px 32px;
          box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
        }
        .features {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 32px;
          margin: 48px 0;
        }
        .feature {
          background: #f8fafc;
          padding: 32px;
          border-radius: 16px;
          border: 1px solid #e2e8f0;
          transition: all 0.2s;
        }
        .feature:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        }
        .feature-icon {
          font-size: 2.5rem;
          margin-bottom: 16px;
          display: block;
        }
        .feature h3 {
          margin: 0 0 12px;
          color: #2d3748;
          font-size: 1.25rem;
        }
        .feature p {
          margin: 0;
          color: #718096;
        }
        .quick-start {
          background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
          border: 1px solid #90cdf4;
          padding: 32px;
          border-radius: 16px;
          margin: 48px 0;
        }
        .quick-start h2 {
          margin: 0 0 16px;
          color: #2c5282;
        }
        .steps {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 24px;
          margin: 24px 0;
        }
        .step {
          background: white;
          padding: 24px;
          border-radius: 12px;
          border-left: 4px solid #4299e1;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .step-number {
          display: inline-block;
          background: #4299e1;
          color: white;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          text-align: center;
          font-weight: bold;
          margin-bottom: 12px;
        }
        .step h4 {
          margin: 0 0 8px;
          color: #2d3748;
        }
        .step p {
          margin: 0;
          color: #718096;
          font-size: 0.9rem;
        }
        .actions {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin: 48px 0;
        }
        .action-btn {
          display: block;
          padding: 16px 24px;
          background: #4a5568;
          color: white;
          text-decoration: none;
          border-radius: 12px;
          text-align: center;
          font-weight: 600;
          transition: all 0.2s;
        }
        .action-btn:hover {
          background: #2d3748;
          transform: translateY(-2px);
        }
        .action-btn.primary {
          background: #4299e1;
        }
        .action-btn.primary:hover {
          background: #3182ce;
        }
        .stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 24px;
          margin: 48px 0;
          text-align: center;
        }
        .stat {
          padding: 24px;
          background: #f8fafc;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
        }
        .stat-number {
          font-size: 2rem;
          font-weight: bold;
          color: #4299e1;
          display: block;
        }
        .stat-label {
          color: #718096;
          font-size: 0.9rem;
          margin-top: 4px;
        }
        @media (max-width: 768px) {
          .hero h1 { font-size: 2.5rem; }
          .hero p { font-size: 1.1rem; }
          .features { grid-template-columns: 1fr; }
          .steps { grid-template-columns: 1fr; }
          .actions { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="hero">
        <h1>🚀 Smart A/B Testing Platform</h1>
        <p>Make data-driven decisions with AI-powered experimentation. Run sophisticated A/B tests with intelligent user assignment and statistical significance testing.</p>
        <a href="/dashboard" class="cta">Start Testing Now</a>
      </div>

      <div class="container">
        <div class="stats">
          <div class="stat">
            <span class="stat-number">ε-Greedy</span>
            <span class="stat-label">ML Algorithm</span>
          </div>
          <div class="stat">
            <span class="stat-number">Z-Test</span>
            <span class="stat-label">Statistics</span>
          </div>
          <div class="stat">
            <span class="stat-number">Real-time</span>
            <span class="stat-label">Results</span>
          </div>
          <div class="stat">
            <span class="stat-number">API</span>
            <span class="stat-label">Integration</span>
          </div>
        </div>

        <div class="features">
          <div class="feature">
            <span class="feature-icon">🧠</span>
            <h3>Smart Assignment</h3>
            <p>AI-powered epsilon-greedy algorithm automatically assigns users to the best performing variant, balancing exploration and exploitation.</p>
          </div>
          <div class="feature">
            <span class="feature-icon">📊</span>
            <h3>Statistical Rigor</h3>
            <p>Two-proportion z-test with confidence intervals ensures your results are statistically significant and actionable.</p>
          </div>
          <div class="feature">
            <span class="feature-icon">⚡</span>
            <h3>Real-time Results</h3>
            <p>Get instant insights with live result calculation and significance testing as data comes in.</p>
          </div>
          <div class="feature">
            <span class="feature-icon">🔧</span>
            <h3>Developer Friendly</h3>
            <p>RESTful API with comprehensive documentation, batch operations, and easy integration with your existing systems.</p>
          </div>
        </div>

        <div class="quick-start">
          <h2>🚀 Get Started in 3 Steps</h2>
          <div class="steps">
            <div class="step">
              <span class="step-number">1</span>
              <h4>Create Experiment</h4>
              <p>Define your test hypothesis and variants using our intuitive dashboard or API.</p>
            </div>
            <div class="step">
              <span class="step-number">2</span>
              <h4>Assign & Track</h4>
              <p>Users are automatically assigned using ML. Track impressions, clicks, and conversions.</p>
            </div>
            <div class="step">
              <span class="step-number">3</span>
              <h4>Analyze Results</h4>
              <p>Get statistically significant results with confidence intervals and actionable insights.</p>
            </div>
          </div>
        </div>

        <div class="actions">
          <a href="/dashboard" class="action-btn primary">🎯 Open Dashboard</a>
          <a href="/quick-demo" class="action-btn">🚀 Run Demo</a>
          <a href="/guide/getting-started" class="action-btn">📚 Learn More</a>
          <a href="/docs" class="action-btn">🔧 API Docs</a>
          <a href="/metrics-explained" class="action-btn">📊 Metrics Guide</a>
          <a href="/faq" class="action-btn">❓ FAQ</a>
        </div>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


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


@app.get("/db-stats", tags=["monitoring"])
def database_stats():
    """
    📊 Database Statistics - Monitor performance and usage.

    **Includes:**
    - Row counts for all tables
    - Database file size
    - Index information
    - Performance metrics

    **Use cases:**
    - Monitor experiment growth
    - Check database performance
    - Plan capacity and scaling
    - Debug performance issues

    **Returns:** Comprehensive database statistics
    """
    from app.database import get_database_stats

    stats = get_database_stats()
    if stats is None:
        return {
            "error": "Unable to retrieve database statistics",
            "timestamp": datetime.utcnow().isoformat()
        }

    return {
        "database_info": stats,
        "performance_tips": [
            "experiments_count > 100: Consider archiving old experiments",
            "events_count > 1M: Monitor query performance",
            f"Database size: {stats.get('database_size_mb', 0)}MB - backup regularly",
            "Use indexes for optimal query performance"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


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
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Quick Demo - Smart A/B Testing</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 24px; background: #eef2ff; color: #0f172a; }}
        .container {{ max-width: 980px; margin: auto; background: white; padding: 32px; border-radius: 18px; box-shadow: 0 20px 60px rgba(15,23,42,0.12); }}
        h1 {{ margin-top: 0; }}
        h2 {{ margin-bottom: 8px; }}
        .section {{ margin: 24px 0; }}
        .info-box {{ background: #f8fafc; border-left: 4px solid #4f46e5; padding: 18px 20px; border-radius: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        .badge {{ display: inline-block; padding: 6px 12px; border-radius: 999px; background: #eef2ff; color: #4338ca; font-weight: 700; margin-right: 8px; }}
        .links a {{ display: inline-block; margin: 10px 12px 10px 0; padding: 10px 16px; background: #4338ca; color: white; text-decoration: none; border-radius: 12px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>✨ Quick Demo - Complete Example</h1>
        <p>This demo created an experiment, assigned 10 users, logged events, and computed results automatically.</p>

        <div class="section info-box">
          <strong>Experiment</strong>
          <p>ID: {demo_exp.id}</p>
          <p>Name: {demo_exp.name}</p>
          <p>Status: completed</p>
        </div>

        <div class="section">
          <h2>User Assignment</h2>
          <p class="badge">Control: {sum(1 for a in assignments if a['variant'] == 'control')}</p>
          <p class="badge">Treatment: {sum(1 for a in assignments if a['variant'] == 'treatment')}</p>
        </div>

        <div class="section">
          <h2>Results Summary</h2>
          <table>
            <tr><th>Variant</th><th>Conversion Rate</th></tr>
            <tr><td>Control</td><td>{results['control']['conversion_rate']:.1%}</td></tr>
            <tr><td>Treatment</td><td>{results['treatment']['conversion_rate']:.1%}</td></tr>
          </table>
          <div class="info-box" style="margin-top:16px;">
            <p><strong>Winner:</strong> {'🎉 Treatment is significantly better!' if results['is_significant'] else 'Need more data'}</p>
            <p><strong>Confidence:</strong> P-Value: {results['p_value']:.4f} (< 0.05 = significant)</p>
            <p><strong>Uplift:</strong> {results['uplift']:+.1%}</p>
          </div>
        </div>

        <div class="section">
          <h2>Next Steps</h2>
          <ul>
            <li>✅ This is how the platform works</li>
            <li>📖 Read <a href="/guide/getting-started">/guide/getting-started</a></li>
            <li>💡 Check <a href="/metrics-explained">/metrics-explained</a></li>
            <li>🎯 Create your real experiment using <strong>POST /experiment</strong></li>
          </ul>
        </div>

        <div class="links">
          <a href="/">Back to Welcome</a>
          <a href="/docs">Open API Docs</a>
        </div>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/guide/getting-started", tags=["tutorial"], response_class=HTMLResponse)
def getting_started_guide():
    """
    📖 INTERACTIVE GUIDE - Learn step-by-step how to use the platform!
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Getting Started - Smart A/B Testing</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 24px; background: #eff6ff; color: #0f172a; }
        .container { max-width: 900px; margin: auto; background: white; padding: 32px; border-radius: 18px; box-shadow: 0 20px 60px rgba(15,23,42,0.12); }
        h1 { margin-top: 0; }
        h2 { margin-bottom: 8px; }
        .step { background: #f8fafc; border-radius: 14px; padding: 18px 22px; margin: 16px 0; }
        .step strong { display: block; margin-bottom: 6px; }
        .link-list a { display: inline-block; margin: 6px 10px 6px 0; padding: 10px 14px; background: #4338ca; color: white; text-decoration: none; border-radius: 10px; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>📖 Getting Started Guide</h1>
        <p>Follow these five easy steps to start using the A/B testing platform.</p>

        <div class="step">
          <strong>Step 1: See it in action</strong>
          <p>Open <a href="/quick-demo">/quick-demo</a> to run a ready-made demo and see the full workflow.</p>
          <p><em>Action:</em> GET <code>/quick-demo</code></p>
        </div>

        <div class="step">
          <strong>Step 2: Create your first experiment</strong>
          <p>Use the experiment endpoint to make a new test.</p>
          <p><em>Action:</em> POST <code>/experiment</code> with <code>{"name": "my_first_test"}</code></p>
        </div>

        <div class="step">
          <strong>Step 3: Assign a user</strong>
          <p>The ML algorithm chooses control or treatment for each user.</p>
          <p><em>Action:</em> GET <code>/assign?user_id=1&amp;experiment_id=YOUR_EXP_ID</code></p>
        </div>

        <div class="step">
          <strong>Step 4: Log user events</strong>
          <p>Track impressions, clicks, and conversions for your assigned user.</p>
          <p><em>Action:</em> POST <code>/event</code> with <code>{"user_id":1,"experiment_id":YOUR_EXP_ID,"variant":"control","event_type":"impression"}</code></p>
        </div>

        <div class="step">
          <strong>Step 5: View results</strong>
          <p>Get experiment metrics and statistical significance.</p>
          <p><em>Action:</em> GET <code>/results?experiment_id=YOUR_EXP_ID</code></p>
        </div>

        <h2>Quick Reference</h2>
        <div class="link-list">
          <a href="/docs">Swagger UI</a>
          <a href="/metrics-explained">Metrics Explained</a>
          <a href="/faq">FAQ</a>
          <a href="/api-guide">API Guide</a>
        </div>

        <div class="step">
          <strong>API commands</strong>
          <ul>
            <li><code>POST /experiment</code> → <code>{"name":"test_name"}</code></li>
            <li><code>GET /assign?user_id=123&amp;experiment_id=1</code></li>
            <li><code>POST /event</code> → <code>{"user_id":123,"experiment_id":1,"variant":"control","event_type":"impression"}</code></li>
            <li><code>POST /event/batch</code> → batch upload many events</code></li>
            <li><code>GET /results?experiment_id=1</code></li>
            <li><code>GET /experiment/1/status</code></li>
          </ul>
        </div>

        <div class="link-list">
          <a href="/">Back to Welcome</a>
          <a href="/quick-demo">Run Demo Again</a>
        </div>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/metrics-explained", tags=["learning"], response_class=HTMLResponse)
def metrics_explained():
    """
    📊 METRICS GUIDE - Understand what each number means!
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Metrics Explained - Smart A/B Testing</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 24px; background: #eff6ff; color: #0f172a; }
        .container { max-width: 900px; margin: auto; background: white; padding: 32px; border-radius: 18px; box-shadow: 0 20px 60px rgba(15,23,42,0.12); }
        h1, h2 { margin-top: 0; }
        .card { background: #f8fafc; border-radius: 14px; padding: 18px 22px; margin: 18px 0; }
        .metric-title { margin-bottom: 8px; font-weight: 700; }
        .metric-description { margin: 0 0 10px; }
        .links a { display: inline-block; margin: 8px 10px 8px 0; padding: 10px 14px; background: #4338ca; color: white; text-decoration: none; border-radius: 10px; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>📊 Metrics Explained</h1>
        <p>Learn what each A/B test metric means so you can make better decisions.</p>

        <div class="card">
          <h2 class="metric-title">Impressions</h2>
          <p class="metric-description">The number of times a variant was shown to users.</p>
          <p>More impressions mean more reliable data.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">Clicks</h2>
          <p class="metric-description">How many users clicked on the variant.</p>
          <p>This shows whether the variant is engaging.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">Conversions</h2>
          <p class="metric-description">How many users completed the goal, like signup or purchase.</p>
          <p>This is the most important outcome for your test.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">CTR (Click-Through Rate)</h2>
          <p class="metric-description">Clicks divided by impressions.</p>
          <p>Example: 100 clicks ÷ 1000 impressions = 10% CTR.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">Conversion Rate</h2>
          <p class="metric-description">Conversions divided by impressions.</p>
          <p>Example: 20 conversions ÷ 1000 impressions = 2% conversion rate.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">Uplift</h2>
          <p class="metric-description">How much better the treatment is compared to control.</p>
          <p>Positive uplift means treatment is winning.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">P-Value</h2>
          <p class="metric-description">The chance the result happened by luck.</p>
          <p>If p &lt; 0.05, your result is usually considered significant.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">Z-Score</h2>
          <p class="metric-description">Statistical strength of the difference between variants.</p>
          <p>Higher magnitude means a stronger signal.</p>
        </div>

        <div class="card">
          <h2 class="metric-title">Is Significant</h2>
          <p class="metric-description">True means you can trust the result with 95% confidence.</p>
          <p>If false, collect more data before making decisions.</p>
        </div>

        <div class="links">
          <a href="/">Back to Welcome</a>
          <a href="/guide/getting-started">Getting Started</a>
          <a href="/faq">FAQ</a>
        </div>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/faq", tags=["learning"], response_class=HTMLResponse)
def faq():
    """
    ❓ FAQ - Answers to common questions!
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>FAQ - Smart A/B Testing</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 24px; background: #f8fafc; color: #111827; }
        .container { max-width: 900px; margin: auto; background: white; padding: 32px; border-radius: 18px; box-shadow: 0 20px 60px rgba(15,23,42,0.12); }
        h1 { margin-top: 0; }
        .faq-item { background: #eff6ff; border-radius: 14px; padding: 18px 22px; margin: 16px 0; }
        .question { font-weight: 700; margin-bottom: 8px; }
        .answer { margin: 0; }
        .links a { display: inline-block; margin: 8px 10px 8px 0; padding: 10px 14px; background: #4338ca; color: white; text-decoration: none; border-radius: 10px; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>❓ FAQ</h1>
        <p>Answers to the most common questions about using the A/B testing API.</p>

        <div class="faq-item">
          <div class="question">How do I get started?</div>
          <p class="answer">Visit <a href="/guide/getting-started">/guide/getting-started</a> or try <a href="/quick-demo">/quick-demo</a> first.</p>
        </div>

        <div class="faq-item">
          <div class="question">What's the difference between control and treatment?</div>
          <p class="answer">Control is the current experience; treatment is the new version you are testing.</p>
        </div>

        <div class="faq-item">
          <div class="question">How many users do I need to run an experiment?</div>
          <p class="answer">Aim for at least 100 impressions per variant, and 1000+ for strong conclusions.</p>
        </div>

        <div class="faq-item">
          <div class="question">What does p_value mean?</div>
          <p class="answer">It tells you how likely the result was due to chance. p &lt; 0.05 means strong confidence.</p>
        </div>

        <div class="faq-item">
          <div class="question">When can I make a decision?</div>
          <p class="answer">When <code>is_significant</code> is true and you have enough data.</p>
        </div>

        <div class="faq-item">
          <div class="question">Can I use the same user in multiple experiments?</div>
          <p class="answer">Yes. Each experiment is independent, so a user can participate in many tests.</p>
        </div>

        <div class="faq-item">
          <div class="question">What's the ML algorithm doing?</div>
          <p class="answer">Epsilon-greedy: 10% random exploration, 90% traffic to the current winner.</p>
        </div>

        <div class="faq-item">
          <div class="question">How do I log multiple events quickly?</div>
          <p class="answer">Use <code>POST /event/batch</code> to upload many events in one request.</p>
        </div>

        <div class="faq-item">
          <div class="question">What if both variants perform the same?</div>
          <p class="answer">If performance is equal, choose the simpler or less expensive variant.</p>
        </div>

        <div class="faq-item">
          <div class="question">Can I run multiple experiments on the same users?</div>
          <p class="answer">Yes. They are independent tests, so users can be part of multiple experiments.</p>
        </div>

        <div class="links">
          <a href="/">Back to Welcome</a>
          <a href="/metrics-explained">Metrics Explained</a>
          <a href="/guide/getting-started">Getting Started</a>
          <a href="/dashboard">Dashboard UI</a>
        </div>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/dashboard", tags=["dashboard"], response_class=HTMLResponse)
def dashboard():
    """
    Dashboard UI for easy browser-based experiment testing.
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>A/B Testing Dashboard</title>
      <style>
        * { box-sizing: border-box; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
          margin: 0;
          padding: 24px;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          color: #1a202c;
          line-height: 1.6;
        }
        .container {
          max-width: 1200px;
          margin: auto;
          background: white;
          padding: 32px;
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        }
        .header {
          text-align: center;
          margin-bottom: 40px;
          padding-bottom: 24px;
          border-bottom: 2px solid #e2e8f0;
        }
        .header h1 {
          margin: 0 0 8px;
          font-size: 2.5rem;
          font-weight: 800;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .header p {
          margin: 0;
          color: #718096;
          font-size: 1.1rem;
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 24px;
          margin-bottom: 32px;
        }
        .card {
          background: #f8fafc;
          border-radius: 16px;
          padding: 24px;
          border: 1px solid #e2e8f0;
          transition: all 0.2s;
          position: relative;
          overflow: hidden;
        }
        .card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        }
        .card.loading {
          pointer-events: none;
          opacity: 0.7;
        }
        .card.loading::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(255,255,255,0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10;
        }
        .card.loading::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 24px;
          height: 24px;
          margin: -12px 0 0 -12px;
          border: 3px solid #e2e8f0;
          border-top: 3px solid #4299e1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          z-index: 11;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .card h2 {
          margin: 0 0 20px;
          color: #2d3748;
          font-size: 1.25rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .card-icon {
          font-size: 1.5rem;
        }
        label {
          display: block;
          margin: 16px 0 6px;
          font-weight: 600;
          color: #4a5568;
          font-size: 0.9rem;
        }
        input, select {
          width: 100%;
          padding: 12px 16px;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          font-size: 1rem;
          transition: all 0.2s;
          background: white;
        }
        input:focus, select:focus {
          outline: none;
          border-color: #4299e1;
          box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }
        input.error {
          border-color: #e53e3e;
        }
        button {
          width: 100%;
          padding: 14px 20px;
          background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          margin-top: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        button:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
        }
        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }
        button.success {
          background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }
        button.error {
          background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
        }
        .note {
          color: #718096;
          font-size: 0.85rem;
          margin-top: 12px;
          line-height: 1.4;
        }
        .output-container {
          background: #1a202c;
          border-radius: 12px;
          padding: 24px;
          margin-top: 32px;
          border: 1px solid #2d3748;
        }
        .output-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .output-title {
          margin: 0;
          color: #e2e8f0;
          font-size: 1.1rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .clear-btn {
          background: #4a5568;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 0.85rem;
          cursor: pointer;
          transition: all 0.2s;
        }
        .clear-btn:hover {
          background: #2d3748;
        }
        .output {
          background: #2d3748;
          border: 1px solid #4a5568;
          border-radius: 8px;
          padding: 16px;
          min-height: 200px;
          max-height: 400px;
          overflow: auto;
          font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
          font-size: 0.85rem;
          line-height: 1.5;
          color: #e2e8f0;
          white-space: pre-wrap;
        }
        .line {
          margin: 4px 0;
          padding: 2px 0;
        }
        .line.info { color: #a0aec0; }
        .line.action { color: #63b3ed; font-weight: 500; }
        .line.success { color: #68d391; font-weight: 500; }
        .line.error { color: #fc8181; font-weight: 500; }
        .line strong { color: #fbb6ce; }
        .footer {
          margin-top: 40px;
          padding-top: 24px;
          border-top: 1px solid #e2e8f0;
          display: flex;
          justify-content: center;
          gap: 16px;
          flex-wrap: wrap;
        }
        .footer a {
          color: #718096;
          text-decoration: none;
          padding: 8px 16px;
          border-radius: 8px;
          transition: all 0.2s;
          font-size: 0.9rem;
        }
        .footer a:hover {
          background: #f8fafc;
          color: #4a5568;
        }
        .tooltip {
          position: relative;
          display: inline-block;
          margin-left: 8px;
          color: #a0aec0;
          cursor: help;
        }
        .tooltip:hover .tooltip-text {
          visibility: visible;
          opacity: 1;
        }
        .tooltip-text {
          visibility: hidden;
          opacity: 0;
          width: 200px;
          background: #2d3748;
          color: #e2e8f0;
          text-align: center;
          border-radius: 6px;
          padding: 8px;
          position: absolute;
          z-index: 1;
          bottom: 125%;
          left: 50%;
          margin-left: -100px;
          font-size: 0.8rem;
          transition: all 0.2s;
        }
        .tooltip-text::after {
          content: '';
          position: absolute;
          top: 100%;
          left: 50%;
          margin-left: -5px;
          border-width: 5px;
          border-style: solid;
          border-color: #2d3748 transparent transparent transparent;
        }
        @media (max-width: 768px) {
          .grid { grid-template-columns: 1fr; }
          .header h1 { font-size: 2rem; }
          .footer { flex-direction: column; align-items: center; }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>📊 A/B Testing Dashboard</h1>
          <p>Create experiments, assign users, log events, and analyze results with real-time insights</p>
        </div>

        <div class="grid">
          <div class="card" id="create-card">
            <h2><span class="card-icon">🧪</span>Create Experiment</h2>
            <label for="exp-name">Experiment Name</label>
            <input id="exp-name" type="text" placeholder="homepage_button_color_test" value="my_experiment" />
            <button type="button" onclick="createExperiment()" id="create-btn">
              <span class="btn-text">Create Experiment</span>
            </button>
            <p class="note">Give your experiment a descriptive name. The ID will be auto-filled in other forms.</p>
          </div>

          <div class="card" id="assign-card">
            <h2><span class="card-icon">🎯</span>Assign User</h2>
            <label for="assign-user-id">User ID</label>
            <input id="assign-user-id" type="number" min="1" value="1" />
            <label for="assign-exp-id">Experiment ID</label>
            <input id="assign-exp-id" type="number" min="1" value="1" />
            <button type="button" onclick="assignUser()" id="assign-btn">
              <span class="btn-text">Assign User</span>
            </button>
            <p class="note">Users are assigned using AI to balance exploration and exploitation for optimal results.</p>
          </div>

          <div class="card" id="event-card">
            <h2><span class="card-icon">📝</span>Log Event</h2>
            <label for="event-user-id">User ID</label>
            <input id="event-user-id" type="number" min="1" value="1" />
            <label for="event-exp-id">Experiment ID</label>
            <input id="event-exp-id" type="number" min="1" value="1" />
            <label for="event-variant">Variant</label>
            <select id="event-variant">
              <option value="control">Control</option>
              <option value="treatment">Treatment</option>
            </select>
            <label for="event-type">Event Type</label>
            <select id="event-type">
              <option value="impression">Impression</option>
              <option value="click">Click</option>
              <option value="conversion">Conversion</option>
            </select>
            <button type="button" onclick="logEvent()" id="event-btn">
              <span class="btn-text">Log Event</span>
            </button>
            <p class="note">Track user interactions: impressions (views), clicks, or conversions (purchases/signups).</p>
          </div>

          <div class="card" id="results-card">
            <h2><span class="card-icon">📈</span>View Results</h2>
            <label for="results-exp-id">Experiment ID</label>
            <input id="results-exp-id" type="number" min="1" value="1" />
            <button type="button" onclick="getResults()" id="results-btn">
              <span class="btn-text">Get Results</span>
            </button>
            <p class="note">View conversion rates, statistical significance, and confidence intervals.
              <span class="tooltip">?
                <span class="tooltip-text">Results include uplift percentage, p-value for significance, and confidence intervals</span>
              </span>
            </p>
          </div>
        </div>

        <div class="output-container">
          <div class="output-header">
            <h3 class="output-title"><span class="card-icon">💻</span>Activity Log</h3>
            <button class="clear-btn" onclick="clearOutput()">Clear Log</button>
          </div>
          <div id="output" class="output">
            <div class="line info">[00:00:00] Ready to start testing! Create an experiment above to begin.</div>
          </div>
        </div>

        <div class="footer">
          <a href="/">← Back to Home</a>
          <a href="/docs">API Documentation</a>
          <a href="/quick-demo">Run Demo</a>
          <a href="/metrics-explained">Metrics Guide</a>
          <a href="/faq">FAQ</a>
        </div>
      </div>

      <script>
        // Enhanced Dashboard JavaScript with loading states and better UX
        console.log('Enhanced Dashboard JavaScript loaded successfully');

        // Global state management
        let lastExperimentId = null;
        let isProcessing = false;

        // Utility functions
        function formatJson(data) {
          return JSON.stringify(data, null, 2);
        }

        function escapeHtml(text) {
          return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }

        function getTimestamp() {
          return new Date().toLocaleTimeString();
        }

        function appendOutput(message, type = 'info') {
          const output = document.getElementById('output');
          const timestamp = getTimestamp();
          const escaped = escapeHtml(message);
          const line = `<div class="line ${type}">[${timestamp}] ${escaped}</div>`;
          output.innerHTML += line;
          output.scrollTop = output.scrollHeight;
        }

        function clearOutput() {
          console.log('Clearing output log');
          const output = document.getElementById('output');
          output.innerHTML = `<div class="line info">[${getTimestamp()}] Activity log cleared. Ready to continue testing!</div>`;
        }

        function setLoading(cardId, buttonId, loading = true) {
          const card = document.getElementById(cardId);
          const button = document.getElementById(buttonId);
          const btnText = button.querySelector('.btn-text');

          if (loading) {
            card.classList.add('loading');
            button.disabled = true;
            btnText.textContent = 'Processing...';
          } else {
            card.classList.remove('loading');
            button.disabled = false;
            btnText.textContent = buttonId.replace('-btn', '').replace('create', 'Create Experiment').replace('assign', 'Assign User').replace('event', 'Log Event').replace('results', 'Get Results');
          }
        }

        function showButtonState(buttonId, state, message = '') {
          const button = document.getElementById(buttonId);
          button.className = `button ${state}`;
          const btnText = button.querySelector('.btn-text');
          if (message) {
            btnText.textContent = message;
            setTimeout(() => {
              btnText.textContent = buttonId.replace('-btn', '').replace('create', 'Create Experiment').replace('assign', 'Assign User').replace('event', 'Log Event').replace('results', 'Get Results');
              button.className = 'button';
            }, 2000);
          }
        }

        function validateInput(inputId, fieldName) {
          const input = document.getElementById(inputId);
          const value = input.value.trim();

          if (!value) {
            input.classList.add('error');
            appendOutput(`Error: ${fieldName} is required`, 'error');
            return false;
          }

          input.classList.remove('error');
          return true;
        }

        // Enhanced API functions with loading states
        async function createExperiment() {
          if (isProcessing) return;
          isProcessing = true;

          console.log('Creating experiment...');
          const nameInput = document.getElementById('exp-name');

          if (!validateInput('exp-name', 'Experiment name')) {
            isProcessing = false;
            return;
          }

          const name = nameInput.value.trim();
          setLoading('create-card', 'create-btn', true);
          appendOutput(`🧪 Creating experiment: "${name}"`, 'action');

          try {
            const response = await fetch('/experiment/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name })
            });

            const data = await response.json();
            console.log('Create experiment response:', response.status, data);

            if (!response.ok) {
              const errorMsg = data.detail || `HTTP ${response.status}: ${response.statusText}`;
              appendOutput(`❌ Failed to create experiment: ${errorMsg}`, 'error');
              showButtonState('create-btn', 'error', 'Failed');
              return;
            }

            appendOutput(`✅ Experiment created successfully! ID: ${data.id}`, 'success');
            showButtonState('create-btn', 'success', 'Created!');

            // Auto-fill experiment ID in other forms
            lastExperimentId = data.id;
            document.getElementById('assign-exp-id').value = data.id;
            document.getElementById('event-exp-id').value = data.id;
            document.getElementById('results-exp-id').value = data.id;

            appendOutput(`🔄 Auto-filled experiment ID (${data.id}) in other forms`, 'info');

          } catch (error) {
            console.error('Create experiment error:', error);
            appendOutput(`❌ Network error: ${error.message}`, 'error');
            showButtonState('create-btn', 'error', 'Error');
          } finally {
            setLoading('create-card', 'create-btn', false);
            isProcessing = false;
          }
        }

        async function assignUser() {
          if (isProcessing) return;
          isProcessing = true;

          console.log('Assigning user...');
          const userId = document.getElementById('assign-user-id').value;
          const expId = document.getElementById('assign-exp-id').value;

          if (!validateInput('assign-user-id', 'User ID') || !validateInput('assign-exp-id', 'Experiment ID')) {
            isProcessing = false;
            return;
          }

          setLoading('assign-card', 'assign-btn', true);
          appendOutput(`🎯 Assigning user ${userId} to experiment ${expId}...`, 'action');

          try {
            const response = await fetch(`/assign/?user_id=${userId}&experiment_id=${expId}`);
            const data = await response.json();
            console.log('Assign user response:', response.status, data);

            if (!response.ok) {
              const errorMsg = data.detail || `HTTP ${response.status}: ${response.statusText}`;
              appendOutput(`❌ Failed to assign user: ${errorMsg}`, 'error');
              showButtonState('assign-btn', 'error', 'Failed');
              return;
            }

            const variant = data.variant;
            const reason = data.assignment_reason || 'Assigned successfully';
            appendOutput(`✅ User ${userId} assigned to: <strong>${variant.toUpperCase()}</strong>`, 'success');
            appendOutput(`📊 Assignment reason: ${reason}`, 'info');
            showButtonState('assign-btn', 'success', 'Assigned!');

            // Auto-fill variant in event form
            document.getElementById('event-variant').value = variant;
            document.getElementById('event-user-id').value = userId;

          } catch (error) {
            console.error('Assign user error:', error);
            appendOutput(`❌ Network error: ${error.message}`, 'error');
            showButtonState('assign-btn', 'error', 'Error');
          } finally {
            setLoading('assign-card', 'assign-btn', false);
            isProcessing = false;
          }
        }

        async function logEvent() {
          if (isProcessing) return;
          isProcessing = true;

          console.log('Logging event...');
          const userId = document.getElementById('event-user-id').value;
          const expId = document.getElementById('event-exp-id').value;
          const variant = document.getElementById('event-variant').value;
          const eventType = document.getElementById('event-type').value;

          if (!validateInput('event-user-id', 'User ID') || !validateInput('event-exp-id', 'Experiment ID')) {
            isProcessing = false;
            return;
          }

          setLoading('event-card', 'event-btn', true);
          appendOutput(`📝 Logging ${eventType} event for user ${userId} (${variant})...`, 'action');

          try {
            const response = await fetch('/event/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                user_id: Number(userId),
                experiment_id: Number(expId),
                variant: variant,
                event_type: eventType
              })
            });

            const data = await response.json();
            console.log('Log event response:', response.status, data);

            if (!response.ok) {
              const errorMsg = data.detail || `HTTP ${response.status}: ${response.statusText}`;
              appendOutput(`❌ Failed to log event: ${errorMsg}`, 'error');
              showButtonState('event-btn', 'error', 'Failed');
              return;
            }

            appendOutput(`✅ Event logged successfully: ${eventType} for user ${userId}`, 'success');
            showButtonState('event-btn', 'success', 'Logged!');

          } catch (error) {
            console.error('Log event error:', error);
            appendOutput(`❌ Network error: ${error.message}`, 'error');
            showButtonState('event-btn', 'error', 'Error');
          } finally {
            setLoading('event-card', 'event-btn', false);
            isProcessing = false;
          }
        }

        async function getResults() {
          if (isProcessing) return;
          isProcessing = true;

          console.log('Getting results...');
          const expId = document.getElementById('results-exp-id').value;

          if (!validateInput('results-exp-id', 'Experiment ID')) {
            isProcessing = false;
            return;
          }

          setLoading('results-card', 'results-btn', true);
          appendOutput(`📈 Fetching results for experiment ${expId}...`, 'action');

          try {
            const response = await fetch(`/results/?experiment_id=${expId}`);
            const data = await response.json();
            console.log('Get results response:', response.status, data);

            if (!response.ok) {
              const errorMsg = data.detail || `HTTP ${response.status}: ${response.statusText}`;
              appendOutput(`❌ Failed to get results: ${errorMsg}`, 'error');
              showButtonState('results-btn', 'error', 'Failed');
              return;
            }

            appendOutput(`✅ Results retrieved for experiment ${expId}`, 'success');
            appendOutput(`📊 ${formatJson(data)}`, 'info');
            showButtonState('results-btn', 'success', 'Loaded!');

          } catch (error) {
            console.error('Get results error:', error);
            appendOutput(`❌ Network error: ${error.message}`, 'error');
            showButtonState('results-btn', 'error', 'Error');
          } finally {
            setLoading('results-card', 'results-btn', false);
            isProcessing = false;
          }
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
          if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
              case 'Enter':
                e.preventDefault();
                // Focus on first empty required field or submit active form
                const activeElement = document.activeElement;
                if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'SELECT') {
                  const card = activeElement.closest('.card');
                  const button = card.querySelector('button');
                  if (button) button.click();
                }
                break;
              case 'l':
                e.preventDefault();
                clearOutput();
                break;
            }
          }
        });

        // Initialize tooltips and enhance UX
        document.addEventListener('DOMContentLoaded', function() {
          appendOutput(`🚀 Dashboard ready! Use Ctrl+Enter to quick-submit forms, Ctrl+L to clear log.`, 'info');

          // Add input validation feedback
          const inputs = document.querySelectorAll('input, select');
          inputs.forEach(input => {
            input.addEventListener('input', function() {
              this.classList.remove('error');
            });
          });
        });
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


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
