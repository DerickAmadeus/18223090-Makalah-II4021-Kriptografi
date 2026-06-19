import requests
import json
import copy

BASE_URL = "http://127.0.0.1:8000/api/v1/secret"

def print_result(scheme, status, message):
    if status == 200:
        print(f"[SUCCESS] {scheme:<25} : HTTP {status} -> {message}")
    elif status == 403 or status == 500:
        print(f"[BLOCKED] {scheme:<25} : HTTP {status} -> {message}")
    else:
        print(f"[UNKNOWN] {scheme:<25} : HTTP {status} -> {message}")

def print_header(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def run_automated_threat_simulation():
    print(f"\n[INITIALIZING AUTOMATED THREAT SIMULATION...]")

    # ==========================================
    # PHASE 1: TOKEN GENERATION (SPLIT)
    # ==========================================
    print_header("PHASE 1: SYSTEM INITIALIZATION (TOKEN SPLIT)")
    
    # 1. TASSA
    tassa_res = requests.post(f"{BASE_URL}/split-tassa", json={
        "secret": "DB_PASS_TASSA_2026", "k": 3, "user_roles": {"1": 0, "101": 1, "301": 2, "302": 2, "303": 2}
    }).json()
    tassa_shares = tassa_res.get("shares", [])
    t_exec = next(s for s in tassa_shares if s["level"] == 0)
    t_mgr = next(s for s in tassa_shares if s["level"] == 1)
    t_emps = [s for s in tassa_shares if s["level"] == 2]
    print_result("Tassa's Birkhoff", 200, "Tokens Generated")

    # 2. WEIGHTED
    w_res = requests.post(f"{BASE_URL}/split-weighted", json={
        "secret": "DB_PASS_WEIGHTED_2026", "k": 5, "user_weights": {"1": 3, "101": 2, "301": 1, "302": 1, "303": 1}
    }).json()
    w_shares = w_res.get("shares_by_user", {})
    print_result("Weighted Multiple Shares", 200, "Tokens Generated")

    # 3. RBAC
    rbac_res = requests.post(f"{BASE_URL}/split", json={
        "secret": "DB_PASS_RBAC_2026", "k": 3, "custom_x_list": [1, 101, 301, 302, 303]
    }).json()
    rbac_shares = rbac_res.get("shares", [])
    r_exec = next(s for s in rbac_shares if s["x"] == 1)
    r_mgr = next(s for s in rbac_shares if s["x"] == 101)
    r_emps = [s for s in rbac_shares if s["x"] >= 301]
    print_result("Application-Layer RBAC", 200, "Tokens Generated")


    # ==========================================
    # PHASE 2: NORMAL RECOVERY (SUCCESS PATH)
    # ==========================================
    print_header("PHASE 2: VALID RECOVERY (STANDARD ACCESS)")
    
    # Tassa (1 Eks, 1 Mgr, 1 Emp)
    t_payload_valid = {"submitted_shares": [t_exec, t_mgr, t_emps[0]]}
    res = requests.post(f"{BASE_URL}/recover-tassa", json=t_payload_valid)
    print_result("Tassa's Birkhoff", res.status_code, res.json().get("secret", "Error"))

    # Weighted (1 Eks(3), 1 Mgr(2) -> Total 5)
    w_payload_valid = {"submitted_shares": {"1": w_shares["1"], "101": w_shares["101"]}}
    res = requests.post(f"{BASE_URL}/recover-weighted", json=w_payload_valid)
    print_result("Weighted Multiple Shares", res.status_code, res.json().get("secret", "Error"))

    # RBAC (1 Eks, 1 Mgr, 1 Emp)
    r_payload_valid = {"shares": [r_exec, r_mgr, r_emps[0]]}
    res = requests.post(f"{BASE_URL}/recover", json=r_payload_valid)
    print_result("Application-Layer RBAC", res.status_code, res.json().get("secret", "Error"))


    # ==========================================
    # PHASE 3: THREAT 1 - TOKEN FORGERY
    # ==========================================
    print_header("PHASE 3: THREAT 1 - TOKEN FORGERY (DATABASE INTERCEPTION)")
    
    # Tassa Forgery
    t_forge = copy.deepcopy(t_payload_valid)
    t_forge["submitted_shares"][0]["y"] = t_forge["submitted_shares"][0]["y"][:-1] + "9"
    res = requests.post(f"{BASE_URL}/recover-tassa", json=t_forge)
    print_result("Tassa's Birkhoff", res.status_code, res.json().get("detail", "Unknown Error"))

    # Weighted Forgery
    w_forge = copy.deepcopy(w_payload_valid)
    w_forge["submitted_shares"]["1"][0]["y"] = w_forge["submitted_shares"]["1"][0]["y"][:-1] + "9"
    res = requests.post(f"{BASE_URL}/recover-weighted", json=w_forge)
    print_result("Weighted Multiple Shares", res.status_code, res.json().get("detail", "Unknown Error"))

    # RBAC Forgery
    r_forge = copy.deepcopy(r_payload_valid)
    r_forge["shares"][0]["y"] = r_forge["shares"][0]["y"][:-1] + "9"
    res = requests.post(f"{BASE_URL}/recover", json=r_forge)
    print_result("Application-Layer RBAC", res.status_code, res.json().get("detail", "Unknown Error"))


    # ==========================================
    # PHASE 4: THREAT 2 - EMPLOYEE COUP
    # ==========================================
    print_header("PHASE 4: THREAT 2 - EMPLOYEE COUP (INSIDER THREAT)")
    
    # Tassa Coup (3 Employees ONLY)
    t_coup = {"submitted_shares": t_emps[:3]}
    res = requests.post(f"{BASE_URL}/recover-tassa", json=t_coup)
    print_result("Tassa's Birkhoff", res.status_code, res.json().get("detail", "Unknown Error"))

    # Weighted Coup (3 Employees ONLY -> Total weight 3)
    w_coup = {"submitted_shares": {"301": w_shares["301"], "302": w_shares["302"], "303": w_shares["303"]}}
    res = requests.post(f"{BASE_URL}/recover-weighted", json=w_coup)
    print_result("Weighted Multiple Shares", res.status_code, res.json().get("detail", "Unknown Error"))

    # RBAC Coup (3 Employees ONLY)
    r_coup = {"shares": r_emps[:3]}
    res = requests.post(f"{BASE_URL}/recover", json=r_coup)
    print_result("Application-Layer RBAC", res.status_code, res.json().get("detail", "Unknown Error"))


if __name__ == "__main__":
    try:
        run_automated_threat_simulation()
        print(f"\n[SUCCESS] ALL SECURITY SIMULATIONS COMPLETED SUCCESSFULLY!\n")
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Cannot connect to API. Is Uvicorn running?\n")