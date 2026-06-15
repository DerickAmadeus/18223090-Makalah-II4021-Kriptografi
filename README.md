# 18223090-Makalah-II4021-Kriptografi


shamir-secret-api/
│
├── app/                        # Direktori utama kode aplikasi
│   ├── __init__.py
│   ├── main.py                 # Titik masuk (entry point) untuk menjalankan server FastAPI
│   ├── api/                    # Menyimpan semua routing/endpoint API
│   │   ├── __init__.py
│   │   └── routes.py           # Endpoint untuk /split dan /recover
│   │
│   ├── core/                   # Logika bisnis dan keamanan utama
│   │   ├── __init__.py
│   │   ├── shamir.py           # Tempat kamu menulis rumus matematika & interpolasi Lagrange
│   │   └── security.py         # Konfigurasi keamanan tambahan (jika ada)
│   │
│   ├── models/                 # Struktur data masukan (request) dan keluaran (response) JSON
│   │   ├── __init__.py
│   │   └── schemas.py          # Menggunakan Pydantic untuk validasi tipe data
│   │
│   └── db/                     # Konfigurasi database (misal: SQLite)
│       ├── __init__.py
│       └── session.py          # Koneksi ke database
│
├── tests/                      # Direktori wajib untuk pengujian (sangat berguna untuk data makalah)
│   ├── __init__.py
│   ├── test_crypto.py          # Script untuk menguji fungsi matematika Shamir
│   └── test_api.py             # Script untuk menguji endpoint split dan recover
│
├── scripts/                    # Script tambahan untuk keperluan eksperimen makalah
│   └── generate_metrics.py     # Script Python untuk simulasi beban (benchmarking) & bikin grafik
│
├── .env                        # File untuk menyimpan variabel rahasia/konfigurasi lokal
├── requirements.txt            # Daftar pustaka Python yang digunakan (fastapi, uvicorn, dll)
├── .gitignore                  # File yang diabaikan oleh Git
└── README.md                   # Dokumentasi singkat cara menjalankan proyek