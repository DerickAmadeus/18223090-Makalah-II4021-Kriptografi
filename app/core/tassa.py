import secrets

PRIME = 2**521 - 1

def _extended_gcd(a, b):
    x, last_x = 0, 1
    y, last_y = 1, 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    return last_x, last_y

def _mod_inverse(k, prime):
    x, y = _extended_gcd(k, prime)
    return x % prime

def _gaussian_elimination(matrix, vector, prime):
    n = len(matrix)
    # Gabungkan matriks M dan vektor V (Augmented Matrix)
    A = [matrix[i] + [vector[i]] for i in range(n)]
    
    for i in range(n):
        # Cari pivot yang tidak nol
        if A[i][i] == 0:
            for j in range(i + 1, n):
                if A[j][i] != 0:
                    A[i], A[j] = A[j], A[i] # Tukar baris
                    break
                    
        pivot = A[i][i]
        if pivot == 0:
            raise ValueError("Singular matrix - quorum not met or shares are linearly dependent.")
            
        # Normalisasi baris pivot menjadi 1
        inv = _mod_inverse(pivot, prime)
        for j in range(i, n + 1):
            A[i][j] = (A[i][j] * inv) % prime
            
        # Buat elemen lain di kolom pivot menjadi 0
        for j in range(n):
            if i != j:
                factor = A[j][i]
                for k in range(i, n + 1):
                    A[j][k] = (A[j][k] - factor * A[i][k]) % prime
                    
    # Hasil akhir (koefisien polinomial) ada di kolom paling kanan
    return [A[i][n] for i in range(n)]

def _compute_derivative_coeff(degree, derivative_level, x, prime):
    if derivative_level > degree:
        return 0
    
    multiplier = 1
    current_power = degree
    for _ in range(derivative_level):
        multiplier = (multiplier * current_power) % prime
        current_power -= 1
        
    x_powered = pow(x, current_power, prime)
    return (multiplier * x_powered) % prime

def split_secret_tassa(secret_str: str, k: int, user_roles: dict):
    secret_int = int.from_bytes(secret_str.encode('utf-8'), byteorder='big')
    if secret_int >= PRIME:
        raise ValueError("Rahasia terlalu panjang.")

    # Buat koefisien polinomial acak derajat k-1
    poly = [secret_int] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
    
    shares = []
    for uid, d_level in user_roles.items():
        if uid == 0:
            raise ValueError("ID tidak boleh 0.")
            
        y_val = 0
        # Evaluasi nilai y berdasarkan tingkat turunannya
        for degree in range(k):
            coeff = poly[degree]
            if coeff == 0: continue
            
            x_factor = _compute_derivative_coeff(degree, d_level, uid, PRIME)
            y_val = (y_val + coeff * x_factor) % PRIME
            
        shares.append({
            "uid": uid,
            "level": d_level,
            "y": y_val
        })
        
    return shares

def recover_secret_tassa(k: int, submitted_shares: list):
    if len(submitted_shares) != k:
        raise ValueError(f"Sistem Birkhoff wajib menerima tepat {k} token untuk membentuk matriks {k}x{k} yang valid.")
        
    matrix = []
    vector = []
    
    for share in submitted_shares:
        uid = share["uid"]
        d_level = share["level"]
        y_val = share["y"]
        
        # Bangun satu baris persamaan linear untuk user ini
        row = []
        for degree in range(k):
            coeff = _compute_derivative_coeff(degree, d_level, uid, PRIME)
            row.append(coeff)
            
        matrix.append(row)
        vector.append(y_val)
        
    # Selesaikan matriks untuk mencari nilai a_0 (rahasia)
    try:
        coefficients = _gaussian_elimination(matrix, vector, PRIME)
        secret_int = coefficients[0] 
    except ValueError as e:
        raise ValueError(f"FAILED TO RECOVER: {e}")
        
    byte_length = (secret_int.bit_length() + 7) // 8
    try:
        secret_str = secret_int.to_bytes(byte_length, byteorder='big').decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("FAILED TO RECOVER: Decoded UTF-8 is corrupted.")
        
    return secret_str

# --- BLOK PENGUJIAN ---
if __name__ == "__main__":
    rahasia = "Birkhoff_Master_2026!"
    k_threshold = 3
    
    # Hierarki: Bos (0), Manager (1), Karyawan (2)
    roles = {
        5: 0,   
        15: 1,  
        40: 2,  
        41: 2   
    }
    
    print("=== IMPLEMENTASI TASSA'S HIERARCHICAL SECRET SHARING ===")
    token_db = split_secret_tassa(rahasia, k_threshold, roles)
    for t in token_db:
        print(f"ID: {t['uid']} | Derivatif Level: {t['level']} | Nilai Y: {t['y']}")
        
    print("\n[+] Skenario Sukses (Bos + Manager + Karyawan):")
    kumpulan_valid = [token_db[0], token_db[1], token_db[2]]
    print(f"Hasil: {recover_secret_tassa(k_threshold, kumpulan_valid)}")
    print("\n[-] Skenario Gagal (Hanya Karyawan):")
    kumpulan_gagal = [token_db[2], token_db[3], token_db[1]]
    try:
        print(f"Hasil: {recover_secret_tassa(k_threshold, kumpulan_gagal)}")
    except ValueError as e:
        print(f"Error: {e}")