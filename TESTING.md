# 🧪 Testing Guide — Smart A/B Testing Platform

## Quick Test (Automated Python Script)

```bash
# Install requests if not already installed
pip install requests

# Run quick test (50 impressions, ~5 seconds)
python3 test_api.py

# Run full test with more data (200 impressions, ~10 seconds)
python3 test_api.py --full
```

**Output:**
```
✅ All tests passed! Platform is working correctly.
```

The automated test script verifies:
- ✅ API health check
- ✅ Experiment creation
- ✅ User assignment (random phase)
- ✅ Event logging (impressions, clicks, conversions)
- ✅ Results aggregation and metrics calculation
- ✅ Bandit algorithm exploitation (favoring better variant)

---

## Manual Testing with curl

Continue below for step-by-step manual testing instructions.

---

```bash
cd /Users/kathleenweng/ab_testing
uvicorn app.main:app --reload
```

Open browser:

```text
http://localhost:8000/docs
```

---

## 2. Create an Experiment

```bash
curl -X POST "http://localhost:8000/experiment/" \
  -H "Content-Type: application/json" \
  -d '{"name":"homepage_test"}'
```

Expected response:

```json
{
  "id": 1,
  "name": "homepage_test",
  "status": "active"
}
```

---

## 3. Assign Users to Variants

```bash
curl "http://localhost:8000/assign/?user_id=1&experiment_id=1"
```

Run multiple times with different user IDs:

```bash
for i in {1..10}; do
  curl -s "http://localhost:8000/assign/?user_id=$i&experiment_id=1"
  echo
done
```

Expected response:

```json
{
  "user_id": 1,
  "experiment_id": 1,
  "variant": "control"
}
```

---

## 4. Log Events

### Log impressions

**Control variant (50 users):**
```bash
for i in {1..50}; do
  curl -s -X POST "http://localhost:8000/event/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$i,\"experiment_id\":1,\"variant\":\"control\",\"event_type\":\"impression\"}"
done
```

**Treatment variant (50 users):**
```bash
for i in {51..100}; do
  curl -s -X POST "http://localhost:8000/event/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$i,\"experiment_id\":1,\"variant\":\"treatment\",\"event_type\":\"impression\"}"
done
```

---

### Log clicks

**Control variant:**
```bash
for i in {1..20}; do
  curl -s -X POST "http://localhost:8000/event/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$i,\"experiment_id\":1,\"variant\":\"control\",\"event_type\":\"click\"}"
done
```

**Treatment variant:**
```bash
for i in {51..80}; do
  curl -s -X POST "http://localhost:8000/event/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$i,\"experiment_id\":1,\"variant\":\"treatment\",\"event_type\":\"click\"}"
done
```

---

### Log conversions

**Control variant:**
```bash
for i in {1..10}; do
  curl -s -X POST "http://localhost:8000/event/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$i,\"experiment_id\":1,\"variant\":\"control\",\"event_type\":\"conversion\"}"
done
```

**Treatment variant:**
```bash
for i in {51..75}; do
  curl -s -X POST "http://localhost:8000/event/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$i,\"experiment_id\":1,\"variant\":\"treatment\",\"event_type\":\"conversion\"}"
done
```

---

## 5. Get Results

```bash
curl "http://localhost:8000/results/?experiment_id=1" | python3 -m json.tool
```

Expected output:

```json
{
  "experiment_id": 1,
  "experiment_name": "homepage_test",
  "control": {
    "impressions": 50,
    "clicks": 20,
    "conversions": 10,
    "ctr": 0.4,
    "conversion_rate": 0.2
  },
  "treatment": {
    "impressions": 50,
    "clicks": 30,
    "conversions": 25,
    "ctr": 0.6,
    "conversion_rate": 0.5
  }
}
```

**Metrics explained:**
- **impressions**: Total times variant was shown
- **clicks**: Total clicks on variant element
- **conversions**: Total completed desired actions
- **ctr**: Click-through rate = clicks / impressions
- **conversion_rate**: Conversion rate = conversions / impressions

---

## 6. Test ML (Bandit Behavior)

After enough data (100+ impressions), the epsilon-greedy bandit algorithm activates. Test variant assignment:

```bash
for i in {200..210}; do
  echo "User $i:"
  curl -s "http://localhost:8000/assign/?user_id=$i&experiment_id=1" | grep -o '"variant":"[^"]*'
done
```

**Expected behavior:**

- **Before 100 impressions**: Random mix of control and treatment (50% exploration)
- **After 100 impressions**: 
  - ~90% of users assigned to **better-performing variant** (exploitation)
  - ~10% of users assigned randomly (exploration)

In the test above with treatment at 50% conversion vs control at 20%, you should see mostly "treatment" assignments.

---

## 7. Manual Testing (Optional)

Use browser Swagger UI:

```text
http://localhost:8000/docs
```

**Steps:**
1. Click on each endpoint
2. Click "Try it out" button
3. Enter parameters and execute
4. View response JSON

**Endpoints to test:**
- `POST /experiment/` - Create experiment
- `GET /assign/` - Test assignment logic
- `POST /event/` - Log events
- `GET /results/` - View metrics

---

## ✅ Success Criteria

- ✅ Experiment created with unique ID
- ✅ Users assigned consistently (same user = same variant)
- ✅ Events logged for all three types (impression/click/conversion)
- ✅ Metrics calculated correctly:
  - CTR = clicks / impressions
  - Conversion rate = conversions / impressions
- ✅ ML assignment favors better-performing variant after 100 impressions
- ✅ Random exploration prevents getting stuck on suboptimal variant

---

## 🧠 Understanding the Bandit Algorithm

### Exploration Phase (< 100 impressions)
```
if impressions < 100:
    assign = random choice (control or treatment)
```
**Why?** Collect diverse data without bias. Both variants are tried fairly.

### Exploitation Phase (≥ 100 impressions)
```
if random() < 0.1:  # 10% of the time
    assign = random choice (explore)
else:  # 90% of the time
    assign = variant with highest conversion rate (exploit)
```
**Why?** Once we have enough data, favor the better variant while maintaining exploration to detect performance shifts.

### Example from Test
- Control: 10% conversion rate (10 / 100 impressions)
- Treatment: 50% conversion rate (25 / 50 impressions)
- Result: New users mostly assigned to treatment ✅

---

## 🚀 Next Steps (Optional Enhancements)

- [ ] Add statistical significance testing (chi-square test, p-value)
- [ ] Add confidence intervals for metrics
- [ ] Create Python simulation script for bulk testing
- [ ] Add JSON export for results
- [ ] Add stopping rules (early winner detection)
- [ ] Add experiment status transitions (active → paused → completed)
- [ ] Add user-friendly dashboard/visualization

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 already in use | Change port: `uvicorn app.main:app --port 8001` |
| Database locked | Delete `test.db` and restart server |
| Experiment not found | Verify experiment_id exists: `curl http://localhost:8000/experiment/1` |
| Wrong variant in assignment | Check data: `curl http://localhost:8000/results/?experiment_id=1` |
| curl command not found | Use: `python3 -c "import requests; ..."` instead |

