from fastapi import APIRouter, HTTPException
from app.models.schemas import SplitRequest, SplitResponse, RecoverRequest, RecoverResponse, ShareItem
from app.core.shamir import split_secret, recover_secret

router = APIRouter()

@router.post("/split", response_model=SplitResponse)
def split_endpoint(req: SplitRequest):
    try:
        # Panggil fungsi inti matematika
        shares_data = split_secret(secret_str=req.secret, k=req.k, custom_x_list=req.custom_x_list)
        
        # Format ke bentuk model Pydantic
        formatted_shares = [ShareItem(x=s[0], y=str(s[1])) for s in shares_data]
        
        return SplitResponse(
            message="Rahasia berhasil dipecah",
            shares=formatted_shares
        )
    except ValueError as e:
        # Mengembalikan status 400 jika input pengguna tidak logis (misal k > n)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")

@router.post("/recover", response_model=RecoverResponse)
def recover_endpoint(req: RecoverRequest):
    try:
        # Konversi list dari BaseModel (JSON) kembali menjadi list of tuples untuk fungsi Shamir
        shares_tuple = [(s.x, int(s.y)) for s in req.shares]
        
        # Panggil fungsi interpolasi Lagrange
        recovered_secret = recover_secret(shares_tuple)
        
        return RecoverResponse(
            message="Rahasia berhasil dipulihkan",
            secret=recovered_secret
        )
    except ValueError as e:
        # Mengembalikan status 403 Forbidden jika token kurang atau salah
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")