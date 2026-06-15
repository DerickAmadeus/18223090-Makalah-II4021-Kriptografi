from pydantic import BaseModel, Field
from typing import List

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