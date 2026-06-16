import requests
import time
import statistics

BASE_URL = "http://127.0.0.1:8000"
SECRET_TEXT = "DB_Production_Pass_2026"
ITERATIONS = 50  # Jumlah pengujian per metode untuk mendapatkan rata-rata yang valid

# --- PAYLOAD UNTUK MASING-MASING METODE ---
payload_rbac = {
    "secret": SECRET_TEXT,
    "k": 3,
    "custom_x_list": [5, 15, 40, 41]
}

payload_weighted = {
    "secret": SECRET_TEXT,
    "k": 7,
    "user_weights": {
        "5": 3,   # Bos
        "15": 2,  # Manager
        "40": 1,  # Karyawan 1
        "41": 1   # Karyawan 2
    }
}

payload_tassa = {
    "secret": SECRET_TEXT,
    "k": 3,
    "user_roles": {
        "5": 0,   # Bos
        "15": 1,  # Manager
        "40": 2,  # Karyawan 1
        "41": 2   # Karyawan 2
    }
}

def benchmark_endpoint(endpoint_path, payload, method_name):
    url = f"{BASE_URL}{endpoint_path}"
    response_times = []
    
    print(f"[*] Menguji {method_name} ({ITERATIONS} iterasi)...", end="", flush=True)
    
    for _ in range(ITERATIONS):
        start_time = time.perf_counter()
        response = requests.post(url, json=payload)
        end_time = time.perf_counter()
        
        if response.status_code == 200:
            # Hitung waktu dalam milidetik
            duration_ms = (end_time - start_time) * 1000
            response_times.append(duration_ms)
        else:
            print(f"\n[!] Error pada iterasi: {response.text}")
            return None
            
    avg_time = statistics.mean(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    
    print(" Selesai!")
    return {
        "method": method_name,
        "avg": avg_time,
        "min": min_time,
        "max": max_time
    }

if __name__ == "__main__":
    print(f"=== MEMULAI BENCHMARKING API (Rahasia: {SECRET_TEXT}) ===\n")
    
    results = []
    
    # 1. API Handling (RBAC / Multiple Shares Biasa)
    res_rbac = benchmark_endpoint("/api/v1/secret/split", payload_rbac, "1. RBAC / Standard SSS")
    if res_rbac: results.append(res_rbac)
        
    # 2. Weighted (Multiple Shares)
    res_weighted = benchmark_endpoint("/api/v1/secret/split-weighted", payload_weighted, "2. Weighted Multiple Shares")
    if res_weighted: results.append(res_weighted)
        
    # 3. Tassa's Hierarchical (Birkhoff)
    res_tassa = benchmark_endpoint("/api/v1/secret/split-tassa", payload_tassa, "3. Tassa's Birkhoff")
    if res_tassa: results.append(res_tassa)
        
    # --- CETAK HASIL ---
    print("\n=== HASIL EKSPERIMEN (Waktu Pemrosesan Split dalam Milidetik) ===")
    print(f"{'Metode':<30} | {'Rata-rata (ms)':<15} | {'Min (ms)':<10} | {'Max (ms)':<10}")
    print("-" * 75)
    for r in results:
        print(f"{r['method']:<30} | {r['avg']:<15.3f} | {r['min']:<10.3f} | {r['max']:<10.3f}")
    print("-" * 75)
    print("\n[+] Data siap diplot ke dalam grafik untuk naskah makalah.")