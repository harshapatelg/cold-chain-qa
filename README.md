# Automated Unit, API, Performance and Security Testing of a Cold-Chain Produce Spoilage Alert Service

**Course:** ISE2501 CA3: Software Testing & Quality Assurence 
**Method 1:** Specialized Tool Exploration & Program Unit/API Testing  
**Academic Term:** 2026  
**Authors:**
- **Harshapatel G** (Roll Number: `[20241ISE0205]`)
- **Sandhya S** (Roll Number: `[20241ISE0207]`)

---

## 1. Project Overview

The **Cold-Chain Produce Spoilage Alert Service** is an automated quality assurance lab project demonstrating multi-paradigm software testing across unit, API, performance, and security dimensions.

The system is a lightweight **FastAPI** service (Python 3.12, thread-safe in-memory storage, zero database overhead) designed to simulate fresh produce logistics telemetry. It ingests temperature and humidity sensor readings for perishable produce batches, computes cumulative thermal abuse duration outside configured safe biological boundaries, scores spoilage risk, and automatically triggers alert notifications to cold-storage facility managers via an SMS alert gateway.

### Core Business Rules & Preconfigured Assumptions
All numerical constants are centralized in `app/config.py` for easy auditability and rapid parameter tuning:
1. **Preloaded Produce Safe Temperature Ranges:**
   - **Tomato:** `10.0 °C` to `15.0 °C`
   - **Leafy Greens:** `0.0 °C` to `4.0 °C`
   - **Mango:** `10.0 °C` to `13.0 °C`
   - *Boundary Rule:* A temperature reading **exactly on a range limit counts as INSIDE** the safe range.
2. **Physical Sensor Boundaries:**
   - **Temperature:** `-40.0 °C` to `60.0 °C`
   - **Relative Humidity:** `0.0 %` to `100.0 %`
3. **Risk Scoring & Level Classification:**
   - `Risk Score`: Total cumulative minutes the batch has spent outside its safe temperature range.
   - `OK`: Risk score `< 30.0` minutes.
   - `WARNING`: `30.0 <= Risk Score < 120.0` minutes (triggers SMS alert).
   - `CRITICAL`: `Risk Score >= 120.0` minutes (triggers urgent escalation SMS alert).
4. **Timestamp & Duplicate Handling:**
   - Rejects readings older than 24 hours (`86,400 seconds`).
   - Rejects future timestamps (allowing up to `5 seconds` clock skew tolerance).
   - **Duplicate Ingestion Rule:** Duplicate readings with the identical `batch_id` and `timestamp` are ignored and do not alter stored state.
5. **HTTP Error Mapping:**
   - `400 Bad Request`: Malformed JSON, empty identifiers, or invalid data types.
   - `401 Unauthorized`: Missing, expired, or tampered JWT bearer tokens.
   - `404 Not Found`: Non-existent batch ID or unknown alert ID.
   - `422 Unprocessable Entity`: Input values violating physical boundaries or business rules.
   - *State Immutability:* Failed requests must never alter stored application state.

---

## 2. Tools and Licensing Table

| Category | Tool | Version | License | Primary Purpose in Project |
|---|---|---|---|---|
| **Service Engine** | FastAPI / Uvicorn | `0.115+` / `0.30+` | MIT | High-performance REST API and telemetry ingest |
| **Authentication** | PyJWT | `2.8+` | MIT | Secure JWT bearer token creation and signature verification |
| **Unit Testing & Mocking**| Python `unittest` + `unittest.mock` | Standard Lib | Python Software Foundation | Equivalence partitioning, boundary tests, SMS gateway mocking |
| **Property-Based Testing**| Hypothesis | `6.110+` | Mozilla Public License (MPL 2.0) | Automated generation of edge-case inputs to prove invariants |
| **Code Coverage** | Coverage.py | `7.6+` | Apache License 2.0 | Statement and branch coverage auditing (target >= 85%) |
| **API Contract Testing** | Karate DSL | `1.4.1` | MIT | BDD-style declarative `.feature` API contract tests |
| **Performance Testing** | Artillery | `2.0.34` | Mozilla Public License (MPL 2.0) | Multi-phase concurrency load testing with SLA assertions |
| **Security Scanning** | OWASP ZAP (Docker) | `stable` | Apache License 2.0 | DAST passive security auditing and OpenAPI vulnerability scans |
| **Static Code Quality** | SonarQube Community | `10.x` | LGPL v3 | Code smells, cognitive complexity, and security hotspot auditing |
| **CI/CD Automation** | GitHub Actions | `v4` | GitHub Terms | Automated multi-job build, test, and artifact archiving pipeline |

---

## 3. Prerequisites

Ensure the following tools are installed on your workstation:
1. **Python 3.12 or higher** (`python --version`)
2. **Node.js LTS (v18+) and npm** (`node --version`, `npm --version`)
3. **Java 17 or higher** (`java -version`) — *Required for Karate DSL*
4. **Docker Desktop** (`docker --version`) — *Required for OWASP ZAP security scans*
5. **Git** (`git --version`)

> [!NOTE]
> **Host Environment Prerequisites Check:**
> - Python and Node.js with Artillery are fully configured in this workspace.
> - If **Java** or **Docker** is not yet installed on your system, follow the step-by-step install instructions below before running Karate or OWASP ZAP.

---

## 4. Installation Steps

### Step 1: Clone Repository
```powershell
# Windows PowerShell
git clone <repository-url>
cd cold-chain-qa
```
```bash
# Linux / macOS Bash
git clone <repository-url>
cd cold-chain-qa
```

### Step 2: Set Up Python Dependencies
```powershell
# Windows PowerShell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
```bash
# Linux / macOS Bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Install Node.js Dependencies (Artillery)
```powershell
# Windows PowerShell / Bash
npm install
```

### Step 4: (If Java 17+ is Missing) Install Java & Download Karate Standalone JAR
To run Karate DSL API tests, Java 17+ is required:
- **Windows:** Install OpenJDK via winget:
  ```powershell
  winget install Microsoft.OpenJDK.17
  ```
  *(Or download Eclipse Adoptium Temurin 17 from https://adoptium.net)*
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt-get update && sudo apt-get install -y openjdk-17-jre-headless
  ```
- **Download Karate Standalone JAR:**
  Download `karate-1.4.1.jar` and save it as `karate.jar` in your workspace root:
  - Download Link: [Karate Labs Release v1.4.1](https://github.com/karatelabs/karate/releases/download/v1.4.1/karate-1.4.1.jar)
  - Or via PowerShell:
    ```powershell
    Invoke-WebRequest -Uri "https://github.com/karatelabs/karate/releases/download/v1.4.1/karate-1.4.1.jar" -OutFile "karate.jar"
    ```
  - Or via Bash:
    ```bash
    curl -L -o karate.jar "https://github.com/karatelabs/karate/releases/download/v1.4.1/karate-1.4.1.jar"
    ```

### Step 5: (If Docker is Missing) Install Docker Desktop
To run OWASP ZAP security scans:
- **Windows / macOS:** Download and install Docker Desktop: [https://docs.docker.com/desktop/](https://docs.docker.com/desktop/)
- Ensure the Docker daemon is running by verifying `docker info`.

---

## 5. Running the Application

Start the FastAPI application on `127.0.0.1:8000`:
```powershell
# Windows PowerShell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
```bash
# Linux / macOS Bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger API documentation is available at: **`http://127.0.0.1:8000/docs`**  
OpenAPI specification is available at: **`http://127.0.0.1:8000/openapi.json`**

### Preloaded Demo Credentials
- Operator: `username: operator_alice` | `password: securepass123`
- Manager: `username: manager_bob` | `password: coldchain2026`

---

## 6. Exact Test Execution Commands & Reports

### 6.1 Unit Tests & Property-Based Testing
Runs Boundary Value Analysis (BVA), Equivalence Partitioning (EP), SMS gateway mocking, and Hypothesis invariant fuzzing:
```powershell
# Windows PowerShell
python -m unittest discover -s tests/unit -v
```
```bash
# Linux / macOS Bash
python -m unittest discover -s tests/unit -v
```

### 6.2 Code Coverage (Statement & Branch Coverage)
Measures branch coverage and exports terminal breakdown and interactive HTML reports:
```powershell
# Windows PowerShell
python -m coverage run --branch --source=app -m unittest discover -s tests/unit
python -m coverage report -m
python -m coverage html -d reports/coverage
```
```bash
# Linux / macOS Bash
python -m coverage run --branch --source=app -m unittest discover -s tests/unit
python -m coverage report -m
python -m coverage html -d reports/coverage
```
- **Output Report:** Open `reports/coverage/index.html` in any web browser.
- **Actual Result:** **93% total coverage**, meeting and exceeding the 85% requirement.

### 6.3 API Contract Testing with Karate DSL
Ensure the FastAPI server is running in a terminal, then in another terminal execute:
```powershell
# Windows PowerShell
java -jar karate.jar tests/api
```
```bash
# Linux / macOS Bash
java -jar karate.jar tests/api
```
- **Output Report:** Automatically saved to `target/karate-reports/karate-summary.html`.

### 6.4 Concurrency Load Testing with Artillery
Ensure the FastAPI server is running on `http://127.0.0.1:8000`, then execute:
```powershell
# Windows PowerShell
npm run test:load
```
```bash
# Linux / macOS Bash
npm run test:load
```
- **Load Profile:**
  - Phase 1 (Warm-up): 10 users/sec for 10 seconds.
  - Phase 2 (Ramp-up): 10 to 100 users/sec over 20 seconds.
  - Phase 3 (Sustained Hold): 100 users/sec for 30 seconds.
- **SLA Thresholds Enforced (`ensure` plugin):**
  - `p95 < 500 ms`
  - `maxErrorRate < 1%`
- **Output Report:** `reports/artillery-report.json`
- **Actual Measured Results:**
  - Total HTTP Requests: **16,800**
  - Virtual Users Completed: **4,200** (0 failed)
  - Mean Latency: **4.3 ms**
  - **p95 Latency: 12.1 ms** (41x faster than SLA limit)
  - Error Rate: **0.00%**

### 6.5 Security Vulnerability Scans with OWASP ZAP
Start the FastAPI server, then execute the automated scanner script:
```powershell
# Windows PowerShell
.\tests\security\run_zap_baseline.ps1
```
```bash
# Linux / macOS Bash
chmod +x tests/security/run_zap_baseline.sh
./tests/security/run_zap_baseline.sh
```
Optional active OpenAPI endpoint scan:
```powershell
# Windows PowerShell
.\tests\security\run_zap_openapi.ps1
```
```bash
# Linux / macOS Bash
chmod +x tests/security/run_zap_openapi.sh
./tests/security/run_zap_openapi.sh
```
- **Output Reports:** `reports/zap-baseline-report.html` and `reports/zap-openapi-report.html`.

### 6.6 SonarQube Community Edition (Optional / Static Code Quality)
To run SonarQube locally via Docker:
```powershell
# Windows PowerShell
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```
```bash
# Linux / macOS Bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```
Navigate to `http://localhost:9000` (default credentials: `admin` / `admin`), create a local project `cold-chain-qa`, and run the SonarScanner CLI:
```powershell
# Windows PowerShell / Bash
sonar-scanner -Dsonar.projectKey=cold-chain-qa -Dsonar.sources=app -Dsonar.tests=tests -Dsonar.python.coverage.reportPaths=reports/coverage.xml
```

---

## 7. How to Enable Seeded Defects (Demonstration)

The project includes 3 deliberate seeded defects labeled in code with `# SEEDED DEFECT`:
- **Defect 1 (`app/rules.py`):** Uses `<=` instead of `<` in `determine_risk_level`, causing exactly 30.0 minutes to incorrectly return `OK` instead of `WARNING`.
- **Defect 2 (`app/rules.py`):** Uses `<=` instead of `<` in `is_outside_safe_range`, treating readings exactly on lower safe temperature boundaries as out-of-range.
- **Defect 3 (`app/auth.py`):** Bypasses HTTP 401 token verification on `GET /alerts`, leaking active alerts to unauthenticated callers.

### Activating the Seeded Defects
```powershell
# Windows PowerShell
$env:SEED_DEFECTS="1,2,3"
python -m unittest discover -s tests/unit -v
```
```bash
# Linux / macOS Bash
export SEED_DEFECTS="1,2,3"
python -m unittest discover -s tests/unit -v
```
**Outcome:** The test suite immediately catches all 3 defects, generating 3 distinct test failures. Full stack traces and root causes are documented in [docs/defect_log.md](file:///c:/Users/harsh/cold-chain-qa/docs/defect_log.md).

### Deactivating the Seeded Defects (Production Correct Code)
```powershell
# Windows PowerShell
$env:SEED_DEFECTS=""
python -m unittest discover -s tests/unit -v
```
```bash
# Linux / macOS Bash
unset SEED_DEFECTS
python -m unittest discover -s tests/unit -v
```
**Outcome:** All 43 tests pass cleanly.

---

## 8. Project Structure

```text
cold-chain-qa/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Automated GitHub Actions CI workflow
├── app/
│   ├── __init__.py
│   ├── auth.py                    # PyJWT token management and 401 middleware
│   ├── config.py                  # Centralized business rules, thresholds, and defect toggles
│   ├── main.py                    # FastAPI route definitions and error handlers
│   ├── notifier.py                # Fake SMS alert gateway (mockable)
│   ├── rules.py                   # Pure functions for spoilage risk score and risk level
│   ├── store.py                   # Thread-safe in-memory store (batches, produce, alerts)
│   └── validators.py              # Pure input validators (temperature, humidity, timestamps)
├── data/
│   └── boundary_cases.csv         # Boundary Value Analysis data set loaded by unit tests
├── docs/
│   ├── defect_log.md              # Formal defect log with steps to reproduce and fixes
│   ├── test_cases.md              # Formal test cases matrix (EP, BVA, PBT, SLAs)
│   └── tool_evaluation.md         # Tool strengths, limitations, and comparative analyses
├── package.json                   # Node.js project configuration (Artillery load tester)
├── package-lock.json
├── README.md                      # Comprehensive laboratory project guide
├── reports/
│   ├── artillery-report.json      # Real Artillery load test aggregate performance metrics
│   └── coverage/                  # Interactive HTML code coverage dashboard
│       └── index.html
├── requirements.txt               # Pinned Python package dependencies
└── tests/
    ├── api/                       # Karate DSL Behavioral API test features
    │   ├── 01_auth.feature
    │   ├── 02_produce.feature
    │   ├── 03_readings.feature
    │   ├── 04_batch_status.feature
    │   ├── 05_alerts.feature
    │   ├── 06_security_tokens.feature
    │   └── karate-config.js
    ├── performance/
    │   └── load.yml               # Artillery load test scenario and SLA assertions
    ├── security/
    │   ├── run_zap_baseline.ps1   # PowerShell automated OWASP ZAP baseline scanner
    │   ├── run_zap_baseline.sh    # Bash automated OWASP ZAP baseline scanner
    │   ├── run_zap_openapi.ps1    # PowerShell automated OWASP ZAP OpenAPI fuzzer
    │   └── run_zap_openapi.sh     # Bash automated OWASP ZAP OpenAPI fuzzer
    └── unit/                      # Python unit and property-based test suites
        ├── __init__.py
        ├── test_api_endpoints.py  # FastAPI integration and state immutability tests
        ├── test_auth.py           # PyJWT token lifecycle and tampering tests
        ├── test_notifier.py       # unittest.mock external gateway tests
        ├── test_property_hypothesis.py # Hypothesis invariant property tests
        ├── test_rules.py          # Boundary and risk calculation unit tests
        └── test_validators.py     # Pure input validator unit tests
```

---

## 9. Known Limitations

1. **In-Memory Volatility:** Application state is stored exclusively in process memory (RAM). Restarting the FastAPI service resets all registered custom produce types and batch history back to preloaded defaults.
2. **Synchronous Notification Model:** While the SMS gateway is simulated and mocked during tests, in production an asynchronous message broker (e.g., Celery, RabbitMQ, AWS SQS) would be recommended to prevent SMS provider latency from impacting telemetry ingestion.
3. **Clock Skew Constraints:** The service enforces a 5-second future timestamp threshold. If distributed sensor hardware exhibits significant clock drift, an NTP synchronization agent or ingest-time timestamping strategy should be configured.
