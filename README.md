
# Comparative Analysis and Implementation of Hierarchical Secret Sharing via REST API for Centralized Credential Security

his project is a REST API built on a *hybrid stateless-stateful* architecture, designed to protect centralized database credentials from insider threats (such as an *"Employee Coup"* scenario). The system implements and compares three secret sharing methods:

1. **Application-Layer RBAC** — Standard Shamir's Secret Sharing with hierarchy validation handled at the application's routing level.
2. **Weighted Secret Sharing** — Mathematically enforces hierarchy through multishare distribution (at the cost of O(W) payload bloat).
3. **Tassa's Birkhoff Interpolation** — The most optimal architecture, locking hierarchy in place using calculus derivative levels (pure function, first derivative, second derivative), leveraging Birkhoff matrices with O(1) space complexity.

The API ensures that the cryptographic math runs *stateless* in RAM, while every transaction is recorded *statefully* via a SHA-256 hash into a SQLite database as a leak-resistant audit log.


## Tech Stack
* **Language:** Python 3
* **Framework API:** FastAPI & Uvicorn
* **Database:** SQLite (Hanya untuk Hash Audit Log)
* **Crypto Modules:** Hashing (SHA-256), Finite Field Arithmetic, Gaussian Elimination
## Directory
```text
shamir-secret-api/
│
├── app/                        # Main application code directory
│   ├── __init__.py
│   ├── main.py                 # FastAPI server entry point
│   ├── api/                    # Holds all API routing/endpoints
│   │   ├── __init__.py
│   │   └── routes.py           # Main endpoints for /split and /recover
│   │
│   ├── core/                   # Core business logic and cryptography
│   │   ├── __init__.py
│   │   ├── shamir.py           # Standard Shamir math & Lagrange interpolation
│   │   ├── tassa.py            # Tassa math & Birkhoff interpolation
│   │   ├── shamir_weighted.py  # WSS logic (Multiple Shares)
│   │   └── security.py         # Hashing module (SHA-256)
│   │
│   ├── models/                 # Request/response JSON structures
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic schemas for API validation
│   │
│   └── db/                     # SQLite database configuration
│       ├── __init__.py
│       └── session.py          # Audit log connection management
│
├── tests/                      # Automated security testing
│   ├── __init__.py
│   ├── test_threats.py         # Automated Threat Simulation (Token Forgery & Employee Coup)
│   └── cek_db.py               # Script for reading and verifying the audit log
│
├── scripts/                    # Additional scripts for paper evaluation metrics
│   └── generate_metrics.py     # Latency benchmarking & O(W) vs O(1) payload analysis script
│
├── .env                        # Local secret variables/configuration
├── requirements.txt            # List of Python dependencies (fastapi, uvicorn, requests, etc.)
├── .gitignore                  # Files ignored by Git
└── README.md                   # Project documentation
```
## API Reference

### 1. Tassa's Birkhoff HSS

#### Generate Tassa Tokens (Split)

Membagi rahasia menjadi beberapa token dengan hierarki berbasis tingkat turunan kalkulus (Birkhoff).

```http
POST /api/v1/secret/split-tassa
```

| Parameter   | Type   | Description |
|-------------|--------|-------------|
| secret      | string | **Required.** Kata sandi atau data rahasia yang ingin diamankan |
| k           | int    | **Required.** Ambang batas (threshold) matematis untuk pemulihan |
| user_roles  | object | **Required.** Dictionary pemetaan UID ke level (0: Executive, 1: Manager, 2: Employee) |

#### Recover Tassa Secret

Memulihkan rahasia asli menggunakan interpolasi matriks Birkhoff.

```http
POST /api/v1/secret/recover-tassa
```

| Parameter        | Type  | Description |
|------------------|-------|-------------|
| submitted_shares | array | **Required.** Kumpulan objek token sah yang terdiri dari `uid`, `level`, dan `y` |

---

### 2. Weighted Multiple Shares

#### Generate Weighted Tokens (Split)

Membagi rahasia dengan memberikan jumlah token koordinat yang berbeda berdasarkan bobot wewenang pengguna.

```http
POST /api/v1/secret/split-weighted
```

| Parameter     | Type   | Description |
|---------------|--------|-------------|
| secret        | string | **Required.** Kata sandi atau data rahasia yang ingin diamankan |
| k             | int    | **Required.** Ambang batas akumulasi bobot (weight threshold) |
| user_weights  | object | **Required.** Dictionary pemetaan UID ke jumlah bobot token (misal: `"1": 3`) |

#### Recover Weighted Secret

Memulihkan rahasia dengan menggabungkan akumulasi token yang memenuhi threshold.

```http
POST /api/v1/secret/recover-weighted
```

| Parameter        | Type   | Description |
|------------------|--------|-------------|
| submitted_shares | object | **Required.** Dictionary pemetaan UID ke kumpulan array koordinat x dan y miliknya |

---

### 3. Application-Layer RBAC (Standard Shamir)

#### Generate RBAC Tokens (Split)

Membagi rahasia secara merata (1 pengguna = 1 kunci) menggunakan algoritma Shamir standar.

```http
POST /api/v1/secret/split
```

| Parameter      | Type   | Description |
|----------------|--------|-------------|
| secret         | string | **Required.** Kata sandi atau data rahasia yang ingin diamankan |
| k              | int    | **Required.** Ambang batas jumlah orang yang dibutuhkan |
| custom_x_list  | array  | **Required.** Array berisi integer (UID) yang akan dijadikan koordinat x |

#### Recover RBAC Secret

Memulihkan rahasia setelah divalidasi oleh logika routing if-else (menghitung jumlah atasan vs bawahan).

```http
POST /api/v1/secret/recover
```

| Parameter | Type  | Description |
|-----------|-------|-------------|
| shares    | array | **Required.** Kumpulan objek token sah yang hanya terdiri dari koordinat x dan y |

## How To Run
**1. Clone this repository:**

```bash
git clone https://github.com/DerickAmadeus/18223090-Makalah-II4021-Kriptografi.git
cd 18223090-Makalah-II4021-Kriptografi
```

**2. Install the required dependencies:**

```bash
pip install -r requirements.txt
```

**3. Start the FastAPI server:**

```bash
uvicorn app.main:app --reload
```

The server will run at `http://127.0.0.1:8000`.
Interactive documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.


## Testing and Threat Simulation

First run the FastAPI server in one terminal, then open a second terminal to execute the following scripts:

**1. Latency Benchmarking & Payload Analysis**

```bash
python scripts/generate_metrics.py
```

**2. Automated Threat Simulation**

```bash
python tests/test_threats.py
```

**3. Audit Log Database Verification**

```bash
python tests/cek_db.py
```
## Authors

- [@DerickAmadeus](https://www.github.com/DerickAmadeus)

