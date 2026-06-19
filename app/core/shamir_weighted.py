import secrets

PRIME = 2**521 - 1

def _eval_at(poly, x, prime):
    accum = 0
    for coeff in reversed(poly):
        accum *= x
        accum += coeff
        accum %= prime
    return accum

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

def split_secret_weighted(secret_str: str, k: int, user_weights: dict):
    """
    Memecah rahasia dengan bobot yang berbeda tiap user.
    user_weights: dictionary {user_id: bobot_token}
    Contoh: {1055: 3, 2041: 2, 3099: 1}
    """
    total_weights = sum(user_weights.values())
    if k > total_weights:
        raise ValueError(f"Nilai k ({k}) tidak boleh lebih besar dari total bobot token yang dibagikan ({total_weights}).")
        
    secret_int = int.from_bytes(secret_str.encode('utf-8'), byteorder='big')
    if secret_int >= PRIME:
        raise ValueError("Rahasia terlalu panjang.")

    # Buat kurva polinomial derajat k-1
    poly = [secret_int] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
    
    user_shares = {}
    
    # Generate shares berdasarkan bobot masing-masing user
    for uid, weight in user_weights.items():
        if uid == 0:
            raise ValueError("User ID tidak boleh 0.")
            
        shares_for_this_user = []
        for i in range(1, weight + 1):
            # Manipulasi nilai x agar unik untuk setiap share dari user yang sama
            # Contoh: UID 1055 bobot 2 -> x1 = 105501, x2 = 105502
            x_val = (uid * 100) + i
            y_val = _eval_at(poly, x_val, PRIME)
            shares_for_this_user.append((x_val, y_val))
            
        user_shares[uid] = shares_for_this_user
        
    return user_shares

def recover_secret_weighted(list_of_user_shares: list):
    """
    Menerima kumpulan token dari beberapa user, lalu meleburnya menjadi 
    titik-titik koordinat standar untuk dihitung Lagrange-nya.
    """
    # Gabungkan (flatten) semua koordinat yang dibawa oleh kumpulan user
    flattened_shares = []
    for user_shares in list_of_user_shares:
        flattened_shares.extend(user_shares)
        
    if len(flattened_shares) < 2:
        raise ValueError("Minimal butuh 2 titik koordinat untuk interpolasi.")
        
    secret_int = 0
    
    for i in range(len(flattened_shares)):
        x_i, y_i = flattened_shares[i]
        
        numerator = 1
        denominator = 1
        for j in range(len(flattened_shares)):
            if i == j: continue
            x_j, y_j = flattened_shares[j]
            numerator = (numerator * (0 - x_j)) % PRIME
            denominator = (denominator * (x_i - x_j)) % PRIME
            
        lagrange_basis = (numerator * _mod_inverse(denominator, PRIME)) % PRIME
        secret_int = (secret_int + y_i * lagrange_basis) % PRIME
        
    byte_length = (secret_int.bit_length() + 7) // 8
    try:
        secret_str = secret_int.to_bytes(byte_length, byteorder='big').decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("Reconstruction failed: Quorum not met or shares are invalid.")
        
    return secret_str


# --- BLOK PENGUJIAN LOKAL UNTUK BUKTI MAKALAH ---
if __name__ == "__main__":
    rahasia_asli = "Data_Nasabah_2026_Aman"
    
    # Konfigurasi: Kita butuh kuorum k=7
    # Bos = Bobot 3
    # Manager = Bobot 2
    # 3 Karyawan = Masing-masing Bobot 1
    aturan_bobot = {
        5: 3,    # Bos (ID 5)
        15: 2,   # Manager (ID 15)
        40: 1,   # Karyawan 1 (ID 40)
        41: 1,   # Karyawan 2 (ID 41)
        42: 1    # Karyawan 3 (ID 42)
    }
    
    print(f"=== SIMULASI WEIGHTED SECRET SHARING ===")
    print(f"Rahasia: {rahasia_asli}")
    print(f"Syarat Kuorum (k) = 7\n")
    
    # Proses Split
    semua_token = split_secret_weighted(rahasia_asli, k=7, user_weights=aturan_bobot)
    
    # 1. Skenario Kudeta: 3 Karyawan Berkumpul (Total Bobot = 3)
    # Secara matematika, k=7 tidak akan tercapai.
    print("[-] Uji Coba 1: Skenario Kudeta (3 Karyawan)")
    token_kudeta = [semua_token[40], semua_token[41], semua_token[42]]
    try:
        hasil = recover_secret_weighted(token_kudeta)
        print(f"Sukses: {hasil}")
    except ValueError as e:
        print(f"Ditolak oleh Matematika: {e}")
        
    # 2. Skenario Normal Atasan Saja: Bos + Manager (Total Bobot = 3 + 2 = 5)
    # Tetap gagal karena 5 < 7
    print("\n[-] Uji Coba 2: Bos dan Manager Saja")
    token_atasan = [semua_token[5], semua_token[15]]
    try:
        hasil = recover_secret_weighted(token_atasan)
        print(f"Sukses: {hasil}")
    except ValueError as e:
        print(f"Ditolak oleh Matematika: {e}")

    # 3. Skenario Sukses: Bos + Manager + 2 Karyawan (Total Bobot = 3 + 2 + 1 + 1 = 7)
    print("\n[+] Uji Coba 3: Kuorum Terpenuhi (Bos + Manager + 2 Karyawan)")
    token_sukses = [semua_token[5], semua_token[15], semua_token[40], semua_token[41]]
    try:
        hasil = recover_secret_weighted(token_sukses)
        print(f"BERHASIL MEMBUKA BRANKAS: {hasil}")
    except ValueError as e:
        print(f"Gagal: {e}")