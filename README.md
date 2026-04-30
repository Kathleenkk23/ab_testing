# 🚀 Smart A/B Testing Platform (with ML + Statistical Significance)

## 📌 Overview

A production-ready A/B testing backend that:

* 🎯 Assigns users to variants (control/treatment)
* 📊 Tracks behavior (impressions, clicks, conversions)
* 🧮 Computes metrics (CTR, conversion rate)
* 🤖 **Learns and optimizes traffic using ML** (epsilon-greedy bandit)
* 📈 **Validates results with statistical significance** (two-proportion z-test)

This mimics real-world experimentation systems used at companies like Meta, Google, and Amazon.

---

## 🧠 Key Features

### 1. A/B Experimentation
* Create experiments with control vs treatment variants
* Deterministic user assignment (same user → same variant)
* Experiment status tracking (active, paused, completed)

### 2. 🤖 ML-Based Assignment (Epsilon-Greedy Bandit)
* **Exploration Phase** (< 100 impressions): Random 50/50 assignment
* **Exploitation Phase** (≥ 100 impressions): 
  - 90% traffic to best-performing variant
  - 10% traffic for continued exploration
* Dynamically shifts traffic toward higher-converting variant

### 3. 📊 Real-Time Metrics
* **Impressions**: Total times variant was shown
* **Clicks**: User interactions
* **Conversions**: Desired outcomes
* **CTR**: Click-through rate (clicks / impressions)
* **Conversion Rate**: Conversions / impressions

### 4. 📈 Statistical Significance Testing
* **Two-proportion z-test** implementation
* Computes:
  - Control & treatment conversion rates
  - **Uplift**: Difference in performance
  - **Z-score**: Statistical test statistic
  - **P-value**: Probability result is due to chance
  - **Significance**: Boolean (p < 0.05)

👉 **Key Insight**: Distinguishes real improvements from random noise. Even if treatment performs 12% better, the result may not be statistically significant!

---

## 🏗️ Architecture

```
User Request
    ↓
Assignment Service (Bandit ML Algorithm)
    ↓
Assign to Variant (control or treatment)
    ↓
Event Logging (impressions, clicks, conversions)
    ↓
Metrics Aggregation + Statistical Testing
    ↓
Results with Significance
```

---

## ⚙️ Tech Stack

* **Backend**: FastAPI (0.104.1)
* **Database**: SQLite + SQLAlchemy ORM
* **ML Logic**: Epsilon-Greedy Bandit Algorithm
* **Statistics**: Two-Proportion Z-Test (SciPy)
* **Validation**: Pydantic
* **Server**: Uvicorn

---

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Server

```bash
uvicorn app.main:app --reload
```

Visit: **http://localhost:8000/docs** for interactive API documentation

---

## 🧪 Example API Flow

### 1. Create Experiment

```bash
curl -X POST http://localhost:8000/experiment/ \
  -H "Content-Type: application/json" \
  -d '{"name":"homepage_redesign"}'
```

**Response:**
```json
{
  "id": 1,
  "name": "homepage_redesign",
  "status": "active"
}
```

---

### 2. Assign Users

```bash
# Assign user 100
curl "http://localhost:8000/assign/?user_id=100&experiment_id=1"

# Assign user 101
curl "http://localhost:8000/assign/?user_id=101&experiment_id=1"
```

**Response:**
```json
{
  "user_id": 100,
  "experiment_id": 1,
  "variant": "control"
}
```

---

### 3. Log Events

```bash
# Log impression for user 100
curl -X POST http://localhost:8000/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 100,
    "experiment_id": 1,
    "variant": "control",
    "event_type": "impression"
  }'

# Log conversion for user 100
curl -X POST http://localhost:8000/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 100,
    "experiment_id": 1,
    "variant": "control",
    "event_type": "conversion"
  }'
```

---

### 4. Get Results (with Statistical Significance)

```bash
curl "http://localhost:8000/results/?experiment_id=1"
```

**Response:**
```json
{
  "experiment_id": 1,
  "experiment_name": "homepage_redesign",
  "control": {
    "impressions": 500,
    "clicks": 150,
    "conversions": 90,
    "ctr": 0.30,
    "conversion_rate": 0.18
  },
  "treatment": {
    "impressions": 500,
    "clicks": 175,
    "conversions": 150,
    "ctr": 0.35,
    "conversion_rate": 0.30
  },
  "control_conversion_rate": 0.18,
  "treatment_conversion_rate": 0.30,
  "uplift": 0.12,
  "z_score": 2.45,
  "p_value": 0.0143,
  "is_significant": true,
  "alpha": 0.05
}
```

---

## 📊 Interpreting Results

| Field | Meaning |
|-------|---------|
| `control_conversion_rate` | 18% of control users converted |
| `treatment_conversion_rate` | 30% of treatment users converted |
| `uplift` | Treatment is 12% better than control |
| `z_score` | 2.45 (positive = treatment better) |
| `p_value` | 0.0143 (1.43% chance result is random) |
| `is_significant` | ✅ TRUE (p < 0.05, 95% confidence) |

**Interpretation**: We can be 95% confident that the treatment variant truly performs better than control.

---

## 🧠 Machine Learning: Epsilon-Greedy Bandit

### Why This Algorithm?

Traditional A/B tests split traffic 50/50 until the experiment ends. This wastes conversions on the losing variant.

**Epsilon-Greedy** learns in real-time:

**Phase 1** (Data Collection: < 100 impressions)
```
User 1 → Random (50% control, 50% treatment)
User 2 → Random (50% control, 50% treatment)
...
User 50 → Random (50% control, 50% treatment)
```

**Phase 2** (Optimization: ≥ 100 impressions)
```
Observed: Treatment converts at 30%, Control at 18%
User 101 → 90% chance treatment, 10% chance control
User 102 → 90% chance treatment, 10% chance control
...
```

**Result**: More users see the better variant, improving overall conversion rate.

---

## 🧮 Statistical Significance: Two-Proportion Z-Test

### Why This Matters

Converting at 18% vs 30% might be:
1. **Real difference** → Statistically significant
2. **Random noise** → Not statistically significant

The z-test answers: "Is this difference real or just luck?"

### The Formula

```
Step 1: Calculate conversion rates
  p1 = control_conversions / control_impressions
  p2 = treatment_conversions / treatment_impressions

Step 2: Pool rates (assume no difference)
  p_pool = (control_conversions + treatment_conversions) /
           (control_impressions + treatment_impressions)

Step 3: Standard error (how much variance to expect)
  SE = sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

Step 4: Z-statistic (how many SEs away from zero)
  z = (p2 - p1) / SE

Step 5: P-value (probability of seeing this by chance)
  p_value = 2 * P(Z > |z|)  # two-tailed test

Step 6: Decision (alpha = 0.05 = 95% confidence)
  significant = p_value < 0.05
```

---

## 📁 Project Structure

```
ab_testing/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # SQLite config & session management
│   ├── models.py               # SQLAlchemy ORM models
│   ├── routes/
│   │   ├── experiment.py       # Experiment creation endpoints
│   │   ├── assign.py           # User assignment endpoint
│   │   ├── event.py            # Event logging endpoint
│   │   └── results.py          # Results & metrics endpoint
│   └── services/
│       ├── assignment.py       # Epsilon-greedy bandit algorithm
│       ├── metrics.py          # Metrics calculation
│       └── stats.py            # Statistical significance testing
├── test_api.py                 # Automated test suite (6/6 passing)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 📊 Sample Workflow

```python
# 1. Create experiment
POST /experiment/ → {"id": 1, "name": "banner_test"}

# 2. Assign 1000 users (bandit algorithm decides variant)
for user in range(1000):
    GET /assign?user_id={user}&experiment_id=1
    → {"variant": "treatment"} or {"variant": "control"}

# 3. Log events (user interactions)
for event in user_events:
    POST /event/ → {user_id, experiment_id, variant, event_type}

# 4. Get results with statistical significance
GET /results/?experiment_id=1
→ {
    control_conversion_rate: 0.18,
    treatment_conversion_rate: 0.30,
    uplift: 0.12,
    p_value: 0.0143,
    is_significant: true
  }
```

---

## 🧪 Running Tests

```bash
python3 test_api.py
```

**Output:**
```
Test 1: Health Check ✅
Test 2: Create Experiment ✅
Test 3: Assign 10 Users ✅
Test 4: Log 100 Events ✅
Test 5: Get Results ✅
Test 6: Bandit Algorithm (favors better variant) ✅

Tests Passed: 6/6
```

---

## 💬 Resume Description

> Built a production-ready A/B testing platform with an epsilon-greedy bandit algorithm for intelligent variant assignment, integrated statistical significance testing (two-proportion z-test) to validate conversion lift, and implemented real-time metrics aggregation. The system demonstrates applied machine learning, experimentation infrastructure, and statistical reasoning for data-driven product decisions.

---

## 🎯 What This Demonstrates

* **System Design**: Multi-tier backend (routes → services → database)
* **Data-Driven Decisions**: Metrics and statistical testing
* **Applied ML**: Epsilon-greedy bandit for online optimization
* **Statistical Rigor**: Distinguishing signal from noise
* **Production Practices**: Error handling, validation, documentation

---

## 🔮 Future Improvements

- **Thompson Sampling**: Bayesian alternative to epsilon-greedy
- **Confidence Intervals**: Upper/lower bounds on metrics
- **Power Analysis**: Sample size calculations
- **Dashboard**: Real-time visualization
- **Distributed**: Kafka for event streaming, Redis for caching
- **Sequential Testing**: Peek at results without bias

---

## 📜 License

MIT

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
