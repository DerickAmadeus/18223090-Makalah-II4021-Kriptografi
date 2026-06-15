from fastapi import APIRouter, HTTPException
from app.models.schemas import SplitRequest, SplitResponse, RecoverRequest, RecoverResponse, ShareItem
from app.core.shamir import split_secret, recover_secret
from app.core.shamir_weighted import split_secret_weighted, recover_secret_weighted
from app.models.schemas import WeightedSplitRequest, WeightedRecoverRequest

router = APIRouter()

@router.post("/split", response_model=SplitResponse)
def split_endpoint(req: SplitRequest):
    try:
        shares_data = split_secret(secret_str=req.secret, k=req.k, custom_x_list=req.custom_x_list)
        formatted_shares = [ShareItem(x=s[0], y=str(s[1])) for s in shares_data]
        
        return SplitResponse(
            message="Rahasia berhasil dipecah",
            shares=formatted_shares
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")

@router.post("/recover", response_model=RecoverResponse)
def recover_endpoint(req: RecoverRequest):
    # 1. Ekstrak 
    submitted_ids = [s.x for s in req.shares]

    # 2. Authority Counting
    count_b = sum(1 for x in submitted_ids if 1 <= x <= 100)    # Bos (ID 1-100)
    count_m = sum(1 for x in submitted_ids if 101 <= x <= 300)   # Manager (ID 101-300)
    count_e = sum(1 for x in submitted_ids if x > 300)          # Karyawan (ID > 300)
    
    # 3. Hierarchy Validation
    authorized = False
    error_msg = ""

    if count_e > 0:
        # ATURAN 1: Employee need at least 2 supervisors (Bos or Manager)
        if (count_b + count_m) >= 2:
            authorized = True
        else:
            error_msg = "Denied : Need at least 2 supervisors."
            
    elif count_m > 0:
        # ATURAN 2: Manager need at least 1 Boss as backup
        if count_b >= 1:
            authorized = True
        else:
            error_msg = "Denied : Manager requires at least 1 Boss as backup."
            
    elif count_b > 0:
        # ATURAN 3: At least 2 Bosses are required to access the secret
        if count_b >= 2:
            authorized = True
        else:
            error_msg = "Denied : At least 2 Boss required to access the secret."
            
    else:
        error_msg = "Denied : Invalid or empty token."

    if not authorized:
        raise HTTPException(status_code=403, detail=error_msg)

    # 4. Jika validasi jabatan lolos, jalankan matematika Shamir's Secret Sharing
    try:
        shares_tuple = [(s.x, int(s.y)) for s in req.shares]
        recovered_secret = recover_secret(shares_tuple)
        
        return RecoverResponse(
            message="Rahasia berhasil dipulihkan",
            secret=recovered_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")


# --- WEIGHTED SSS ---

@router.post("/split-weighted")
def split_weighted_endpoint(req: WeightedSplitRequest):
    try:
        # Panggil fungsi inti Shamir Weighted
        shares_data = split_secret_weighted(req.secret, req.k, req.user_weights)
        
        # Format response agar nilai Y menjadi string (menghindari error JavaScript)
        formatted_response = {}
        for uid, shares_list in shares_data.items():
            formatted_response[uid] = [{"x": s[0], "y": str(s[1])} for s in shares_list]
            
        return {
            "message": "Rahasia berhasil dipecah dengan sistem bobot",
            "k_required": req.k,
            "shares_by_user": formatted_response
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")

@router.post("/recover-weighted")
def recover_weighted_endpoint(req: WeightedRecoverRequest):
    """
    PERHATIKAN: Tidak ada satupun statemen if-else untuk mengecek jabatan di sini!
    Semua keamanan dikunci murni oleh perhitungan matematika kurva k=7.
    """
    try:
        # Susun kembali data dari request Pydantic menjadi list of lists of tuples
        # Format yang dibutuhkan shamir_2: [ [(x, y), (x, y)], [(x, y)] ]
        list_of_user_shares = []
        for uid, shares_list in req.submitted_shares.items():
            user_tuples = [(s.x, int(s.y)) for s in shares_list]
            list_of_user_shares.append(user_tuples)
            
        # Panggil interpolasi Lagrange matematika
        recovered_secret = recover_secret_weighted(list_of_user_shares)
        
        return {
            "message": "Brankas Utama Berhasil Dibuka!",
            "secret": recovered_secret
        }
    except ValueError as e:
        # Jika kuorum bobot kurang dari 7 (misal kudeta 3 karyawan)
        raise HTTPException(status_code=403, detail=f"Akses Ditolak Matematika: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")
