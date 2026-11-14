# Formal Test Cases Specification

**Course:** ISE2501 CA3: Software Testing & QA  
**Method 1:** Specialized Tool Exploration & Program Unit/API Testing  
**Project:** Cold-Chain Produce Spoilage Alert Service  
**Authors:** Harshapatel G ([Roll No: PLACEHOLDER]) & Sandhya S ([Roll No: PLACEHOLDER])  

---

## 1. Summary of Test Suites

| Suite ID | Scope | Framework / Tool | Technique | Total Cases | Status |
|---|---|---|---|---|---|
| **TS-UNIT-VAL** | Input Validators | `unittest` + CSV Data Provider | Boundary Value Analysis (BVA), Equivalence Partitioning (EP), Type Safety | 15 | PASS |
| **TS-UNIT-RUL** | Risk & Spoilage Rules | `unittest` + CSV Data Provider | Boundary Value Analysis, State Transition, Time Interval Accumulation | 7 | PASS |
| **TS-UNIT-AUT** | JWT Auth & Tokens | `unittest` | Equivalence Partitioning, Tampering, Signature Checks | 7 | PASS |
| **TS-UNIT-NOT** | SMS Alert Gateway | `unittest.mock` | Mocking, Parameter Verification, Failure Injection | 4 | PASS |
| **TS-UNIT-HYP** | Invariant Properties | `Hypothesis` | Property-Based Testing (PBT), Fuzzing (100 runs/prop) | 3 (300 cases) | PASS |
| **TS-UNIT-API** | Endpoint Integration | `TestClient` | Integration, State Immutability, Error Mapping | 11 | PASS |
| **TS-API-KAR** | End-to-End API Workflows | `Karate DSL` | Behavior-Driven API Contracts, Token Propagation | 16 | READY (Java dep) |
| **TS-PERF-ART** | Load & Concurrency | `Artillery` | Multi-phase Ramp Load (10 to 100 VU/s, 16.8k reqs) | 4 Checks | PASS |
| **TS-SEC-ZAP** | Passive & API Security | `OWASP ZAP` Docker | Security Baseline Scan, Passive Header Auditing | Automated Script | READY (Docker dep) |

---

## 2. Unit & Integration Test Cases Specification

| Test Case ID | Component | Technique | Input Values | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| **TC-VAL-001** | `validate_temperature` | BVA (Lower Min - 0.1) | `-40.1` °C | `ValueError` (outside [-40, 60] °C) | `ValueError` raised | **PASS** |
| **TC-VAL-002** | `validate_temperature` | BVA (Exact Min) | `-40.0` °C | Accepted, returns `-40.0` | Returns `-40.0` | **PASS** |
| **TC-VAL-003** | `validate_temperature` | BVA (Lower Min + 0.1) | `-39.9` °C | Accepted, returns `-39.9` | Returns `-39.9` | **PASS** |
| **TC-VAL-004** | `validate_temperature` | EP (Nominal) | `20.0` °C | Accepted, returns `20.0` | Returns `20.0` | **PASS** |
| **TC-VAL-005** | `validate_temperature` | BVA (Upper Max - 0.1) | `59.9` °C | Accepted, returns `59.9` | Returns `59.9` | **PASS** |
| **TC-VAL-006** | `validate_temperature` | BVA (Exact Max) | `60.0` °C | Accepted, returns `60.0` | Returns `60.0` | **PASS** |
| **TC-VAL-007** | `validate_temperature` | BVA (Upper Max + 0.1) | `60.1` °C | `ValueError` (outside [-40, 60] °C) | `ValueError` raised | **PASS** |
| **TC-VAL-008** | `validate_temperature` | Negative (Type Safety) | `True`, `"25.0"`, `None` | `TypeError` raised | `TypeError` raised | **PASS** |
| **TC-VAL-009** | `validate_humidity` | BVA (Lower Min - 0.1) | `-0.1` % | `ValueError` (outside [0, 100] %) | `ValueError` raised | **PASS** |
| **TC-VAL-010** | `validate_humidity` | BVA (Exact Min Boundary)| `0.0` % | Accepted, returns `0.0` | Returns `0.0` | **PASS** |
| **TC-VAL-011** | `validate_humidity` | BVA (Upper Max Boundary)| `100.0` % | Accepted, returns `100.0` | Returns `100.0` | **PASS** |
| **TC-VAL-012** | `validate_humidity` | BVA (Upper Max + 0.1) | `100.1` % | `ValueError` (outside [0, 100] %) | `ValueError` raised | **PASS** |
| **TC-VAL-013** | `validate_produce_range`| Inverted Range BVA | `min=15.0`, `max=10.0` °C | `ValueError` ("min cannot be greater than max") | `ValueError` raised | **PASS** |
| **TC-VAL-014** | `validate_timestamp` | Clock Skew Tolerance | `now + 3 seconds` | Accepted within 5s skew tolerance | Accepted | **PASS** |
| **TC-VAL-015** | `validate_timestamp` | Future Age Constraint | `now + 60 seconds` | `ValueError` ("cannot be in future") | `ValueError` raised | **PASS** |
| **TC-VAL-016** | `validate_timestamp` | Expiry Age Constraint | `now - 24h 1min` | `ValueError` ("older than 24h limit") | `ValueError` raised | **PASS** |
| **TC-RUL-001** | `is_outside_safe_range`| Tomato Safe Lower -0.01| `9.99` °C (range [10, 15]) | Returns `True` (outside range) | Returns `True` | **PASS** |
| **TC-RUL-002** | `is_outside_safe_range`| Tomato Safe Lower Limit| `10.0` °C (range [10, 15]) | Returns `False` (exact limit counts as inside) | Returns `False` | **PASS** |
| **TC-RUL-003** | `is_outside_safe_range`| Tomato Safe Upper Limit| `15.0` °C (range [10, 15]) | Returns `False` (exact limit counts as inside) | Returns `False` | **PASS** |
| **TC-RUL-004** | `is_outside_safe_range`| Tomato Safe Upper +0.01| `15.01` °C (range [10, 15]) | Returns `True` (outside range) | Returns `True` | **PASS** |
| **TC-RUL-005** | `determine_risk_level` | BVA Just Below Warning | `29.99` minutes | Returns `"OK"` | Returns `"OK"` | **PASS** |
| **TC-RUL-006** | `determine_risk_level` | BVA Exact Warning Limit | `30.00` minutes | Returns `"WARNING"` | Returns `"WARNING"` | **PASS** |
| **TC-RUL-007** | `determine_risk_level` | BVA Exact Critical Limit| `120.00` minutes | Returns `"CRITICAL"` | Returns `"CRITICAL"` | **PASS** |
| **TC-AUT-001** | `authenticate_user` | Demo Operator Auth | `operator_alice`, `securepass123` | Returns `True` | Returns `True` | **PASS** |
| **TC-AUT-002** | `authenticate_user` | Invalid Password | `operator_alice`, `wrong` | Returns `False` | Returns `False` | **PASS** |
| **TC-AUT-003** | `create_access_token` | Token Lifecycle | `{"sub": "operator_alice"}` | Returns valid signed JWT | Returns valid JWT | **PASS** |
| **TC-AUT-004** | `decode_access_token` | Signature Tampering | Altered HMAC secret signature | `ValueError` ("Invalid token") | `ValueError` raised | **PASS** |
| **TC-AUT-005** | `decode_access_token` | Expired Token | Expiration `now - 10 min` | `ValueError` ("Token has expired") | `ValueError` raised | **PASS** |
| **TC-AUT-006** | `require_auth` | Missing Auth Header | `Authorization: None` | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASS** |
| **TC-NOT-001** | `send_alert` | SMS Gateway Normal | `phone="+15551234567"`, text | Returns `True`, appends sent record | Returns `True`, logged | **PASS** |
| **TC-NOT-002** | `send_alert` | Negative Empty Phone | `phone=""` | `ValueError` ("cannot be empty") | `ValueError` raised | **PASS** |
| **TC-NOT-003** | `send_spoilage_sms` | External Mocking | Mocked `send_alert` gateway | Called once with correct phone & template | `assert_called_once` matched | **PASS** |
| **TC-NOT-004** | `send_spoilage_sms` | Gateway Outage Handling| Mocked gateway timeout | `RuntimeError` propagated cleanly | `RuntimeError` raised | **PASS** |
| **TC-HYP-001** | `calculate_risk_score` | Invariant Property PBT | Arbitrary sequences of 0-20 readings | Invariant: `risk_score >= 0.0` | Passed 100 generated cases | **PASS** |
| **TC-HYP-002** | `determine_risk_level` | Monotonicity PBT | Durations `0 <= m1 <= m2 <= 500` min | Invariant: `Rank(Lvl(m1)) <= Rank(Lvl(m2))` | Passed 100 generated cases | **PASS** |
| **TC-HYP-003** | `validate_temperature` | Universal Rejection PBT| Floats `[-10000, -40.0001] U [60.0001, 10000]`| Invariant: Always raises `ValueError` | Passed 100 generated cases | **PASS** |
| **TC-API-001** | `POST /login` | API Authentication | Valid credentials | HTTP 200, JWT token returned | HTTP 200, JWT returned | **PASS** |
| **TC-API-002** | `POST /login` | Negative Credentials | Wrong password | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASS** |
| **TC-API-003** | Protected Endpoints | Security Enforcement | Request without Bearer token | HTTP 401 Unauthorized on all routes | HTTP 401 Unauthorized | **PASS** |
| **TC-API-004** | `POST /produce` | Custom Range Ingestion | `strawberry`, `1.0` to `4.0` °C | HTTP 201 Created | HTTP 201 Created | **PASS** |
| **TC-API-005** | `POST /produce` | Invalid Range (min > max)| `strawberry`, `10.0` to `2.0` °C | HTTP 422 Unprocessable Entity | HTTP 422 Unprocessable Entity | **PASS** |
| **TC-API-006** | `POST /readings` | Telemetry Ingest | Valid tomato reading | HTTP 201 Created, `accepted` status | HTTP 201 Created | **PASS** |
| **TC-API-007** | `POST /readings` | Out-of-Bounds Sensor | `temperature_c = 99.0` | HTTP 422 Unprocessable Entity | HTTP 422 Unprocessable Entity | **PASS** |
| **TC-API-008** | `POST /readings` | Duplicate Ingestion | Same `batch_id` and `timestamp` | HTTP 200 OK, `ignored` status, count = 1 | HTTP 200 OK, count = 1 | **PASS** |
| **TC-API-009** | State Immutability | Negative Ingestion | Invalid temperature `999.0` | HTTP 422; Batch not created in store | HTTP 422; 404 on batch status | **PASS** |
| **TC-API-010** | `GET /batches/{id}/status`| Status Retrieval | Non-existent batch ID | HTTP 404 Not Found | HTTP 404 Not Found | **PASS** |
| **TC-API-011** | Full Alert Lifecycle | Telemetry + Acknowledge | 45 min out-of-range readings | Alert created (`ACTIVE`), ack changes to `ACKNOWLEDGED` | HTTP 200, status updated | **PASS** |

---

## 3. Performance & Load Test Cases (Artillery)

| Test Case ID | Target Endpoint | Load Profile | SLA / Threshold | Actual Result | Status |
|---|---|---|---|---|---|
| **TC-PERF-001** | Full User Journey (`/login` -> `/readings` -> `/batches` -> `/alerts`) | Warm-up (10 VU/s, 10s) -> Ramp-up (10 to 100 VU/s, 20s) -> Sustained Hold (100 VU/s, 30s) | Error Rate < 1% | **0.00% error rate** (0 vusers failed out of 4,200) | **PASS** |
| **TC-PERF-002** | Full User Journey | Total 16,800 requests executed across 4,200 virtual users | p95 Latency < 500 ms | **p95 = 12.1 ms** (41x faster than threshold) | **PASS** |
| **TC-PERF-003** | Endpoints under peak concurrency (100 VU/s) | Sustained 100 users/sec creating 400 req/sec | Mean response time < 50 ms | **Mean = 4.3 ms**, **Median = 3.0 ms** | **PASS** |
| **TC-PERF-004** | Latency tail distribution | Peak throughput: 297 requests/second | p99 Latency < 1000 ms | **p99 = 27.9 ms** | **PASS** |
