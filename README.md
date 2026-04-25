# Smart A/B Testing Platform

A production-ready A/B testing platform with machine learning-based user assignment using an epsilon-greedy bandit algorithm.

## Features

- **Create Experiments**: Define A/B tests with control and treatment variants
- **Intelligent Assignment**: Epsilon-greedy bandit algorithm automatically optimizes variant selection based on conversion performance
- **Event Tracking**: Log impressions, clicks, and conversions for detailed user behavior analysis
- **Real-time Metrics**: Compute aggregated results including CTR, conversion rates, and statistical summaries

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Validation**: Pydantic
- **Server**: Uvicorn

## Project Structure

```
ab_testing/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration and session management
│   ├── models.py            # SQLAlchemy database models
│   ├── routes/
│   │   ├── experiment.py    # Experiment creation endpoints
│   │   ├── assign.py        # User assignment with bandit algorithm
│   │   ├── event.py         # Event logging endpoints
│   │   └── results.py       # Results and metrics endpoints
│   └── services/
│       ├── assignment.py    # Epsilon-greedy bandit logic
│       └── metrics.py       # Metrics calculation service
├── requirements.txt         # Project dependencies
└── README.md               # This file
```

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Server

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Create Experiment

**POST** `/experiment/`

Create a new A/B testing experiment.

**Request:**
```json
{
  "name": "homepage_banner_v1"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "homepage_banner_v1",
  "status": "active"
}
```

---

### 2. Assign User to Variant

**GET** `/assign?user_id=123&experiment_id=1`

Assign a user to an experiment variant using epsilon-greedy bandit algorithm.

**Logic:**
- **Exploration Phase** (< 100 impressions): Random assignment
- **Exploitation Phase** (≥ 100 impressions):
  - 10% of time: Random assignment (explore)
  - 90% of time: Assign to variant with higher conversion rate (exploit)

**Response:**
```json
{
  "user_id": 123,
  "experiment_id": 1,
  "variant": "treatment"
}
```

---

### 3. Log Event

**POST** `/event/`

Track user behavior (impressions, clicks, conversions).

**Request:**
```json
{
  "user_id": 123,
  "experiment_id": 1,
  "variant": "treatment",
  "event_type": "click"
}
```

**Event Types:**
- `impression`: User was shown the variant
- `click`: User clicked on the variant element
- `conversion`: User completed the desired action

**Response:**
```json
{
  "id": 1,
  "user_id": 123,
  "experiment_id": 1,
  "variant": "treatment",
  "event_type": "click"
}
```

---

### 4. Get Results

**GET** `/results?experiment_id=1`

Retrieve aggregated metrics for an experiment.

**Response:**
```json
{
  "experiment_id": 1,
  "experiment_name": "homepage_banner_v1",
  "control": {
    "impressions": 1050,
    "clicks": 315,
    "conversions": 94,
    "ctr": 0.3,
    "conversion_rate": 0.0895
  },
  "treatment": {
    "impressions": 980,
    "clicks": 308,
    "conversions": 107,
    "ctr": 0.3143,
    "conversion_rate": 0.1092
  }
}
```

## Machine Learning: Epsilon-Greedy Bandit

The assignment service implements a simple but effective bandit algorithm:

### Algorithm

```
if total_impressions < 100:
    variant = random_choice(['control', 'treatment'])
else:
    if random() < epsilon (0.1):
        variant = random_choice(['control', 'treatment'])  # Explore
    else:
        variant = variant_with_highest_conversion_rate()  # Exploit
```

### Parameters

- **epsilon**: 0.1 (10% exploration rate)
- **MIN_IMPRESSIONS**: 100 (minimum data before exploitation starts)

### Benefits

1. **Initial Exploration**: Random assignment during startup ensures diverse data collection
2. **Continuous Learning**: Dynamically switches to high-performing variants as data accumulates
3. **Balanced Approach**: Maintains 10% exploration to catch performance changes and unexpected patterns
4. **Simple & Interpretable**: Easy to understand and debug business decisions

## Usage Example

```bash
# 1. Create an experiment
curl -X POST http://localhost:8000/experiment/ \
  -H "Content-Type: application/json" \
  -d '{"name": "button_color_test"}'

# Response: {"id": 1, "name": "button_color_test", "status": "active"}

# 2. Assign a user (ML-based)
curl "http://localhost:8000/assign?user_id=12345&experiment_id=1"

# Response: {"user_id": 12345, "experiment_id": 1, "variant": "treatment"}

# 3. Log an impression event
curl -X POST http://localhost:8000/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 12345,
    "experiment_id": 1,
    "variant": "treatment",
    "event_type": "impression"
  }'

# 4. Log a conversion event
curl -X POST http://localhost:8000/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 12345,
    "experiment_id": 1,
    "variant": "treatment",
    "event_type": "conversion"
  }'

# 5. Get results
curl "http://localhost:8000/results?experiment_id=1"
```

## Key Design Decisions

1. **Modular Architecture**: Separated concerns into routes and services for maintainability
2. **Database-Driven**: All events and assignments persisted for audit trail and future analysis
3. **Idempotent Assignment**: Users get the same variant across multiple assignment calls
4. **No Frontend**: Focused on backend API design and ML logic
5. **Simple Database**: SQLite for easy local development and testing

## Testing the Platform

### Quick Start

Run the server and use the Swagger UI at `/docs` to test endpoints interactively.

```bash
uvicorn app.main:app --reload
# Then visit http://localhost:8000/docs
```

### Comprehensive Testing Guide

See [TESTING.md](TESTING.md) for a complete step-by-step guide including:

- Creating experiments
- Assigning users with the bandit algorithm
- Logging events (impressions, clicks, conversions)
- Viewing aggregated results
- Testing ML behavior after sufficient data
- Manual browser testing
- Troubleshooting common issues

### Quick Test with Python Script

```bash
# Run quick test (uses ~50 impressions)
python3 test_api.py

# Run full test with more data (uses ~200 impressions)
python3 test_api.py --full
```

The test script automatically:
- ✅ Creates an experiment
- ✅ Assigns users to variants
- ✅ Logs events (impressions, clicks, conversions)
- ✅ Retrieves and displays results
- ✅ Tests ML bandit algorithm behavior
- ✅ Verifies the algorithm favors high-converting variants

### Quick Test with curl

```bash
# 1. Create experiment
curl -X POST "http://localhost:8000/experiment/" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_experiment"}'

# 2. Assign users
for i in {1..10}; do
  curl -s "http://localhost:8000/assign/?user_id=$i&experiment_id=1"
done

# 3. Log events (impressions)
for i in {1..50}; do
  curl -s -X POST "http://localhost:8000/event/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$i,\"experiment_id\":1,\"variant\":\"control\",\"event_type\":\"impression\"}"
done

# 4. View results
curl "http://localhost:8000/results/?experiment_id=1" | python3 -m json.tool
```

## Resume Description

**Built an A/B testing platform with a bandit-based assignment system (epsilon-greedy) that dynamically optimizes variant selection based on user conversion behavior.** The platform includes a FastAPI backend with SQLAlchemy ORM, real-time event tracking, and intelligent user segmentation using machine learning. Implemented exploration-exploitation balance to continuously improve variant performance while maintaining statistical rigor.

## Future Enhancements

- Statistical significance testing
- Bayesian bandit algorithms
- Multi-armed bandit support (3+ variants)
- Experiment scheduling and automatic stopping rules
- Analytics dashboard
- A/A testing for validation
- Rate limiting and API authentication

## License

MIT
