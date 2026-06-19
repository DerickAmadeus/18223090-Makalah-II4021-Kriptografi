from fastapi import FastAPI
from app.api.routes import router
from app.db.session import init_db

init_db()

app = FastAPI(
    title="Shamir's Secret Sharing API",
    description="API untuk memecah dan merekonstruksi kredensial rahasia menggunakan threshold cryptography.",
    version="1.0.0"
)

# Daftarkan router yang sudah kita buat
app.include_router(router, prefix="/api/v1/secret", tags=["Secret Sharing Operations"])

@app.get("/")
def root():
    return {"message": "Server API Shamir's Secret Sharing berjalan dengan baik."}