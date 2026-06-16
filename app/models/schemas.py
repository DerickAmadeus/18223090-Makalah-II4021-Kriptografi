from pydantic import BaseModel, Field
from typing import List
from typing import Dict, Any

class ShareItem(BaseModel):
    x: int
    y: str

class SplitRequest(BaseModel):
    secret: str = Field(..., description="Teks rahasia yang ingin disembunyikan")
    k: int = Field(..., description="Batas minimum (threshold) token untuk membuka rahasia")
    custom_x_list: List[int] = Field(..., description="Daftar ID unik pemegang token (tidak boleh 0)")

    # Tambahkan blok ini agar Swagger UI otomatis mengisi JSON-nya
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "secret": "DB_Production_Pass_2026",
                    "k": 3,
                    "custom_x_list": [1055, 2041, 3099, 4120, 5088]
                }
            ]
        }
    }

class RecoverRequest(BaseModel):
    shares: List[ShareItem] = Field(..., description="Daftar token (minimal sejumlah k) untuk membuka rahasia")

    # Tambahkan blok ini untuk endpoint recover
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "shares": [
                        {
                            "x": 1055,
                            "y": "Ketik_nilai_y_disini"
                        },
                        {
                            "x": 3099,
                            "y": "Ketik_nilai_y_disini"
                        },
                        {
                            "x": 5088,
                            "y": "Ketik_nilai_y_disini"
                        }
                    ]
                }
            ]
        }
    }

# (Bawahnya untuk SplitResponse dan RecoverResponse biarkan seperti biasa)
class SplitResponse(BaseModel):
    message: str
    shares: List[ShareItem]

class RecoverResponse(BaseModel):
    message: str
    secret: str


# --- Skema untuk Weighted Shamir's Secret Sharing ---

class WeightedSplitRequest(BaseModel):
    secret: str = Field(..., description="Teks rahasia yang ingin disembunyikan")
    k: int = Field(..., description="Batas minimum bobot kuorum (misal: 7)")
    user_weights: Dict[int, int] = Field(
        ..., 
        description="Dictionary ID User dan Bobotnya. Format: {User_ID: Bobot}"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "secret": "Data_Nasabah_2026_Aman",
                "k": 7,
                "user_weights": {
                    5: 3,   # Bos (ID 5) punya bobot 3
                    15: 2,  # Manager (ID 15) punya bobot 2
                    40: 1,  # Karyawan 1 (ID 40) punya bobot 1
                    41: 1,  # Karyawan 2 (ID 41) punya bobot 1
                    42: 1   # Karyawan 3 (ID 42) punya bobot 1
                }
            }]
        }
    }

class WeightedRecoverRequest(BaseModel):
    # Format input: Dictionary berisi kumpulan array ShareItem dari masing-masing user
    submitted_shares: Dict[int, List[ShareItem]]

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "submitted_shares": {
                    "5": [
                        {"x": 501, "y": "string_panjang_dari_split"},
                        {"x": 502, "y": "string_panjang_dari_split"},
                        {"x": 503, "y": "string_panjang_dari_split"}
                    ],
                    "15": [
                        {"x": 1501, "y": "string_panjang_dari_split"},
                        {"x": 1502, "y": "string_panjang_dari_split"}
                    ]
                }
            }]
        }
    }

# --- SKEMA UNTUK TASSA'S SECRET SHARING ---

class TassaSplitRequest(BaseModel):
    secret: str = Field(..., description="Teks rahasia yang ingin disembunyikan")
    k: int = Field(..., description="Dimensi matriks kuorum (misal: 3)")
    user_roles: Dict[int, int] = Field(
        ..., 
        description="Format: {User_ID: Level_Turunan}. Bos = 0, Manager = 1, Karyawan = 2"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "secret": "Birkhoff_Master_2026!",
                "k": 3,
                "user_roles": {
                    5: 0,   # Bos (Titik Potong)
                    15: 1,  # Manager (Turunan ke-1)
                    40: 2,  # Karyawan 1 (Turunan ke-2)
                    41: 2   # Karyawan 2 (Turunan ke-2)
                }
            }]
        }
    }

class TassaShareItem(BaseModel):
    uid: int
    level: int
    y: str

class TassaRecoverRequest(BaseModel):
    # Tassa wajib menerima tepat 'k' buah objek token
    submitted_shares: List[TassaShareItem] = Field(..., description="Wajib berisi tepat sejumlah k token")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "submitted_shares": [
                    {"uid": 5, "level": 0, "y": "string_panjang_hasil_split_bos"},
                    {"uid": 15, "level": 1, "y": "string_panjang_hasil_split_manager"},
                    {"uid": 40, "level": 2, "y": "string_panjang_hasil_split_karyawan"}
                ]
            }]
        }
    }