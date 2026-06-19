import requests
import time
import statistics

BASE_URL = "http://127.0.0.1:8000"
SECRET_TEXT = "DB_Production_Pass_2026"
ITERATIONS = 50  

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
    
    token_count = 0
    avg_token_length = 0
    
    print(f"[*] Menguji {method_name} ({ITERATIONS} iterasi)...", end="", flush=True)
    
    for i in range(ITERATIONS):
        start_time = time.perf_counter()
        response = requests.post(url, json=payload)
        end_time = time.perf_counter()
        
        if response.status_code == 200:
            duration_ms = (end_time - start_time) * 1000
            response_times.append(duration_ms)
            
            # Hitung jumlah dan panjang token HANYA pada iterasi pertama (karena ukurannya konstan)
            if i == 0:
                data = response.json()
                total_chars = 0
                
                # Parsing untuk RBAC dan Tassa (format array "shares")
                if "shares" in data:
                    shares = data["shares"]
                    token_count = len(shares)
                    total_chars = sum(len(str(s["y"])) for s in shares)
                    
                # Parsing untuk Weighted (format object "shares_by_user")
                elif "shares_by_user" in data:
                    for uid, shares_list in data["shares_by_user"].items():
                        token_count += len(shares_list)
                        total_chars += sum(len(str(s["y"])) for s in shares_list)
                        
                avg_token_length = total_chars / token_count if token_count > 0 else 0
                
        else:
            print(f"\n[!] Error pada iterasi: {response.text}")
            return None
            
    avg_time = statistics.mean(response_times)
    
    print(" Selesai!")
    return {
        "method": method_name,
        "avg_ms": avg_time,
        "token_count": token_count,
        "avg_length": avg_token_length
    }


if __name__ == "__main__":
    print(f"=== MEMULAI BENCHMARKING & ANALISIS PAYLOAD API (Rahasia: {SECRET_TEXT}) ===\n")
    
    results = []
    
    res_rbac = benchmark_endpoint("/api/v1/secret/split", payload_rbac, "1. RBAC / Standard SSS")
    if res_rbac: results.append(res_rbac)
        
    res_weighted = benchmark_endpoint("/api/v1/secret/split-weighted", payload_weighted, "2. Weighted Multiple Shares")
    if res_weighted: results.append(res_weighted)
        
    res_tassa = benchmark_endpoint("/api/v1/secret/split-tassa", payload_tassa, "3. Tassa's Birkhoff")
    if res_tassa: results.append(res_tassa)
        
    # --- CETAK HASIL ---
    print("\n=== HASIL EKSPERIMEN (Waktu Pemrosesan & Efisiensi Payload) ===")
    print(f"{'Metode':<30} | {'Latency (ms)':<15} | {'Jml Token (Total)':<20} | {'Rata-rata Panjang Token (Karakter)':<35}")
    print("-" * 110)
    for r in results:
        print(f"{r['method']:<30} | {r['avg_ms']:<15.3f} | {r['token_count']:<20} | {r['avg_length']:<35.0f}")
    print("-" * 110)
    print("\n[+] Data siap dianalisis untuk mendukung argumen Space Complexity O(1) vs O(W).")