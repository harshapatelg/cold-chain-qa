# Defect Log and Seeded Defect Demonstration

**Course:** ISE2501 CA3: Software Testing & QA  
**Method 1:** Specialized Tool Exploration & Program Unit/API Testing  
**Project:** Cold-Chain Produce Spoilage Alert Service  
**Authors:** Harshapatel G ([Roll No: PLACEHOLDER]) & Sandhya S ([Roll No: PLACEHOLDER])  

---

## 1. Summary of Defect Management

As required by the assignment guidelines, the Cold-Chain service implements 3 deliberate, seeded defects controlled by the environment variable `SEED_DEFECTS`. When `SEED_DEFECTS` is populated (e.g. `SEED_DEFECTS="1,2,3"`), the defects activate to demonstrate test suite efficacy in catching boundary, logic, and security vulnerabilities. When the environment variable is unset or empty, the codebase executes strictly correct production logic.

### Defect Tracking Summary Table

| Defect ID | Seeded? | Title | Module Affected | Severity | Priority | Test That Caught It | Retest Status |
|---|---|---|---|---|---|---|---|
| **DEF-001** | Yes | Boundary Operator Inversion at 30-min Warning Threshold | `app/rules.py` (`determine_risk_level`) | High | High | `test_rules.py::test_risk_level_thresholds_from_csv` | **VERIFIED FIXED** |
| **DEF-002** | Yes | Off-by-one Lower Temperature Bound Classification | `app/rules.py` (`is_outside_safe_range`) | Critical | High | `test_rules.py::test_temperature_limit_boundaries_from_csv` | **VERIFIED FIXED** |
| **DEF-003** | Yes | Missing 401 Authorization Enforcement on `GET /alerts` | `app/auth.py` (`require_auth`) | Critical | High | `test_api_endpoints.py::test_endpoints_require_authentication` | **VERIFIED FIXED** |

---

## 2. Detailed Defect Reports

### Defect DEF-001: Boundary Operator Inversion at 30-Minute Threshold

- **Defect ID:** `DEF-001`
- **Seeded (Yes/No):** Yes (Controlled via `SEED_DEFECTS="1"`)
- **Severity:** High (Functional Business Logic)
- **Priority:** High
- **Component:** `app/rules.py` -> `determine_risk_level()`
- **Steps to Reproduce:**
  1. Set environment variable: `$env:SEED_DEFECTS="1"` (or `export SEED_DEFECTS="1"`).
  2. Call `determine_risk_level(30.0)` for a produce batch that accumulated exactly 30.0 minutes outside its safe range.
  3. Observe the returned risk level string.
- **Expected Result:**
  Per rule specification: "Level is OK below 30 minutes, WARNING from 30, CRITICAL from 120."
  At exactly `30.0` minutes, the function must return `"WARNING"`.
- **Actual Real Test Failure Output:**
  ```text
  FAIL: test_risk_level_thresholds_from_csv (test_rules.TestRules.test_risk_level_thresholds_from_csv) 
  [Exact WARNING threshold boundary (30.0 min)] (minutes=30.0, expected='WARNING')
  Traceback (most recent call last):
    File "C:\Users\harsh\cold-chain-qa\tests\unit\test_rules.py", line 62, in test_risk_level_thresholds_from_csv
      self.assertEqual(level, expected_lvl)
  AssertionError: 'OK' != 'WARNING'
  - OK
  + WARNING
  ```
- **Root Cause:**
  When Defect 1 is active, line 94 of `app/rules.py` uses `minutes_outside_range <= THRESHOLD_OK_MAX_MINUTES` instead of `< THRESHOLD_OK_MAX_MINUTES`. Consequently, at the exact boundary value of 30.0 minutes, the batch is misclassified as `"OK"` instead of triggering a `"WARNING"`, delaying alert dispatch to facility managers.
- **Fix:**
  Replace the `<=` operator with `<`:
  ```python
  if minutes_outside_range < THRESHOLD_OK_MAX_MINUTES:
      return "OK"
  elif minutes_outside_range < THRESHOLD_WARNING_MAX_MINUTES:
      return "WARNING"
  else:
      return "CRITICAL"
  ```
- **Retest Result:**
  Re-tested with `SEED_DEFECTS=""`. Test ran and passed (`OK`, 0.009s).

---

### Defect DEF-002: Off-by-One at Lower Temperature Boundary Limit

- **Defect ID:** `DEF-002`
- **Seeded (Yes/No):** Yes (Controlled via `SEED_DEFECTS="2"`)
- **Severity:** Critical (Data Integrity & False Alerting)
- **Priority:** High
- **Component:** `app/rules.py` -> `is_outside_safe_range()`
- **Steps to Reproduce:**
  1. Set environment variable: `$env:SEED_DEFECTS="2"`.
  2. Ingest a sensor reading for tomato (configured safe range `[10.0, 15.0]` °C) where `temperature_c = 10.0` °C.
  3. Evaluate `is_outside_safe_range(10.0, 10.0, 15.0)`.
- **Expected Result:**
  Per rule specification: "A reading exactly on a range limit counts as inside the range."
  `is_outside_safe_range` must return `False`.
- **Actual Real Test Failure Output:**
  ```text
  FAIL: test_temperature_limit_boundaries_from_csv (test_rules.TestRules.test_temperature_limit_boundaries_from_csv) 
  [Tomato exact lower safe boundary (10.0 C)] (temp=10.0, expected='INSIDE')
  Traceback (most recent call last):
    File "C:\Users\harsh\cold-chain-qa\tests\unit\test_rules.py", line 46, in test_temperature_limit_boundaries_from_csv
      self.assertFalse(is_outside, f"Expected {val} C to be INSIDE [{min_c}, {max_c}]")
  AssertionError: True is not false : Expected 10.0 C to be INSIDE [10.0, 15.0]
  ```
- **Root Cause:**
  When Defect 2 is active, line 32 of `app/rules.py` evaluates:
  ```python
  return (temperature_c <= min_temp_c) or (temperature_c > max_temp_c)
  ```
  The `<=` operator flags readings exactly on `min_temp_c` as outside the safe range, causing false positive spoilage score accumulation.
- **Fix:**
  Strict inequality `<` must be used at the lower boundary:
  ```python
  return (temperature_c < min_temp_c) or (temperature_c > max_temp_c)
  ```
- **Retest Result:**
  Re-tested with `SEED_DEFECTS=""`. Test ran and passed (`OK`).

---

### Defect DEF-003: Missing 401 Authentication Enforcement on `GET /alerts`

- **Defect ID:** `DEF-003`
- **Seeded (Yes/No):** Yes (Controlled via `SEED_DEFECTS="3"`)
- **Severity:** Critical (Information Disclosure / Broken Access Control - OWASP A01)
- **Priority:** High
- **Component:** `app/auth.py` -> `require_auth()`
- **Steps to Reproduce:**
  1. Set environment variable: `$env:SEED_DEFECTS="3"`.
  2. Send an unauthenticated HTTP GET request to `/alerts` with no `Authorization` header.
- **Expected Result:**
  Per security contract: "All endpoints except /login need a valid token."
  Endpoint must reject the request with HTTP `401 Unauthorized`.
- **Actual Real Test Failure Output:**
  ```text
  FAIL: test_endpoints_require_authentication (test_api_endpoints.TestApiEndpoints.test_endpoints_require_authentication) 
  (method='GET', path='/alerts')
  Traceback (most recent call last):
    File "C:\Users\harsh\cold-chain-qa\tests\unit\test_api_endpoints.py", line 67, in test_endpoints_require_authentication
      self.assertEqual(res.status_code, 401, f"Endpoint {path} did not enforce 401 authentication")
  AssertionError: 200 != 401 : Endpoint /alerts did not enforce 401 authentication
  ```
- **Root Cause:**
  When Defect 3 is active, line 68 of `app/auth.py` intercepts requests to `/alerts`:
  ```python
  if is_defect_active(3) and path == "/alerts" and request.method == "GET":
      return {"sub": "unauthenticated_guest", "role": "bypass"}
  ```
  This creates an intentional security vulnerability by bypassing token verification, allowing unauthenticated third parties to read proprietary spoilage alert data.
- **Fix:**
  Remove the bypass condition so all paths mandate token verification:
  ```python
  auth_header = request.headers.get("Authorization")
  if not auth_header or not auth_header.startswith("Bearer "):
      raise HTTPException(status_code=401, detail="Missing or invalid Authorization header...")
  ```
- **Retest Result:**
  Re-tested with `SEED_DEFECTS=""`. Test ran and passed (`OK`), returning HTTP 401 on missing tokens across all protected routes.
