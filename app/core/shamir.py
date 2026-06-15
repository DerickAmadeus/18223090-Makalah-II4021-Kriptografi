import secrets

# Kita menggunakan Prime ke-13 Mersenne (2^521 - 1) sebagai batas Finite Field.
# Angka ini sangat besar dan aman untuk mengenkripsi string hingga ~64 karakter.
PRIME = 2**521 - 1

def _eval_at(poly, x, prime):
    """Mengevaluasi polinomial pada titik x menggunakan skema Horner."""
    accum = 0
    for coeff in reversed(poly):
        accum *= x
        accum += coeff
        accum %= prime
    return accum

def _extended_gcd(a, b):
    """Extended Euclidean Algorithm untuk mencari modular inverse."""
    x, last_x = 0, 1
    y, last_y = 1, 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    return last_x, last_y

def _mod_inverse(k, prime):
    """Mencari inverse dari k modulo prime (k^-1 mod prime)."""
    x, y = _extended_gcd(k, prime)
    return x % prime

def split_secret(secret_str: str, k: int, custom_x_list: list):
    """
    Memecah string rahasia menggunakan daftar ID (x) yang ditentukan pengguna.
    custom_x_list: list berisi angka integer unik (misal ID pegawai) yang tidak boleh 0.
    """
    n = len(custom_x_list)
    
    if k > n:
        raise ValueError("Nilai k (threshold) tidak boleh lebih besar dari jumlah shares yang diminta.")
        
    # Validasi input list pengguna
    if 0 in custom_x_list:
        raise ValueError("Nilai x (ID Share) tidak boleh bernilai 0, karena 0 adalah titik rahasia.")
    
    if len(set(custom_x_list)) != n:
        raise ValueError("Semua nilai x (ID Share) harus unik, tidak boleh ada yang duplikat.")
        
    # 1. Konversi string teks rahasia menjadi format angka (integer)
    secret_int = int.from_bytes(secret_str.encode('utf-8'), byteorder='big')
    
    if secret_int >= PRIME:
        raise ValueError("Rahasia terlalu panjang. Maksimal sekitar 64 karakter.")

    # 2. Buat persamaan polinomial derajat k-1 secara acak
    poly = [secret_int] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
    
    # 3. Buat koordinat (shares) menggunakan nilai x dari list pengguna
    shares = []
    for x in custom_x_list:
        y = _eval_at(poly, x, PRIME)
        shares.append((x, y))
        
    return shares

def recover_secret(shares: list):
    """
    Merekonstruksi rahasia dari sekumpulan shares menggunakan Interpolasi Lagrange.
    """
    if len(shares) < 2:
        raise ValueError("Minimal butuh 2 shares untuk dapat melakukan interpolasi.")
        
    secret_int = 0
    
    # Menghitung Interpolasi Lagrange pada titik x = 0
    for i in range(len(shares)):
        x_i, y_i = shares[i]
        
        numerator = 1
        denominator = 1
        for j in range(len(shares)):
            if i == j:
                continue
            x_j, y_j = shares[j]
            
            # Hitung pembilang dan penyebut untuk basis Lagrange
            numerator = (numerator * (0 - x_j)) % PRIME
            denominator = (denominator * (x_i - x_j)) % PRIME
            
        # Kalikan nilai y dengan bobot Lagrange, lalu jumlahkan
        lagrange_basis = (numerator * _mod_inverse(denominator, PRIME)) % PRIME
        secret_int = (secret_int + y_i * lagrange_basis) % PRIME
        
    # 4. Konversi kembali dari angka (integer) menjadi teks string
    byte_length = (secret_int.bit_length() + 7) // 8
    try:
        secret_str = secret_int.to_bytes(byte_length, byteorder='big').decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("Gagal merekonstruksi. Kemungkinan jumlah shares kurang atau tidak valid.")
        
    return secret_str

# --- BLOK PENGUJIAN LOKAL ---
if __name__ == "__main__":
    rahasia_asli = "DB_Master_Pass_2026!"
    print(f"=== Skenario Normal ===")
    print(f"Rahasia Asli: {rahasia_asli}")
    
    # KITA TENTUKAN SENDIRI ID SHARE-NYA
    id_karyawan = [1055, 2041, 3099, 4120, 5088]
    
    # Kita pecah butuh 3 orang untuk buka (k=3)
    shares = split_secret(rahasia_asli, k=3, custom_x_list=id_karyawan)

    # Tampilkan shares yang dihasilkan
    print("\nShares yang dihasilkan:")
    for idx, (x, y) in enumerate(shares):
        print(f"Share {idx+1}: ID={x}, Value={y}")
    
    # 1. SKENARIO SUKSES (3 Orang Kumpul)
    print("\n[+] Menguji dengan 3 Token (Memenuhi Kuorum)...")
    token_sukses = [shares[0], shares[2], shares[4]]
    try:
        hasil = recover_secret(token_sukses)
        print(f"BERHASIL DIBUKA: {hasil}")
    except Exception as e:
        print(f"GAGAL: {e}")
        
    # 2. SKENARIO GAGAL / KACAU (Hanya 2 Orang Kumpul)
    print("\n[-] Menguji dengan 2 Token (Kurang dari Kuorum)...")
    token_kurang = [shares[1], shares[3]] # Hanya ID 2041 dan 4120
    
    try:
        # Kita panggil fungsi internal mod_inverse dan Lagrange secara manual 
        # hanya untuk melihat "angka kacau" yang dihasilkan sebelum error
        
        secret_int_kacau = 0
        for i in range(len(token_kurang)):
            x_i, y_i = token_kurang[i]
            num, den = 1, 1
            for j in range(len(token_kurang)):
                if i == j: continue
                x_j, _ = token_kurang[j]
                num = (num * (0 - x_j)) % PRIME
                den = (den * (x_i - x_j)) % PRIME
            basis = (num * _mod_inverse(den, PRIME)) % PRIME
            secret_int_kacau = (secret_int_kacau + y_i * basis) % PRIME
            
        print(f"HASIL MATEMATIKA KACAU (Integer): {secret_int_kacau}")
        
        # Coba jalankan fungsi recover aslinya yang akan trigger error handler
        hasil_gagal = recover_secret(token_kurang)
        print(f"BERHASIL DIBUKA: {hasil_gagal}")
    except ValueError as e:
        print(f"HANDLER MENCEGAH AKSES: {e}")