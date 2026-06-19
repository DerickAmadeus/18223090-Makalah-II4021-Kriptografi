from fastapi import APIRouter, HTTPException
from app.models.schemas import SplitRequest, SplitResponse, RecoverRequest, RecoverResponse, ShareItem
from app.core.shamir import split_secret, recover_secret
from app.core.shamir_weighted import split_secret_weighted, recover_secret_weighted
from app.models.schemas import WeightedSplitRequest, WeightedRecoverRequest
from app.core.tassa import split_secret_tassa, recover_secret_tassa
from app.models.schemas import TassaSplitRequest, TassaRecoverRequest, TassaShareItem

from app.core.security import hash_token
from app.db.session import insert_split_log, insert_recover_log, verify_token_hash

router = APIRouter()

# --- RBAC / STANDARD SSS ---

@router.post("/split", response_model=SplitResponse)
def split_endpoint(req: SplitRequest):
    try:
        shares_data = split_secret(secret_str=req.secret, k=req.k, custom_x_list=req.custom_x_list)
        formatted_shares = []
        
        for s in shares_data:
            uid = s[0]
            token_string = str(s[1])
            
            if 1 <= uid <= 100: role = 0      
            elif 101 <= uid <= 300: role = 1  
            else: role = 2                    
            
            t_hash = hash_token(token_string)
            insert_split_log(uid=uid, role_level=role, token_hash=t_hash, algorithm="RBAC", status="SUCCESS")
            
            formatted_shares.append(ShareItem(x=uid, y=token_string))
        
        return SplitResponse(message="Rahasia berhasil dipecah.", shares=formatted_shares)
    except Exception:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")

@router.post("/recover", response_model=RecoverResponse)
def recover_endpoint(req: RecoverRequest):
    valid_tokens = []
    
    for share in req.shares:
        t_hash = hash_token(share.y)
        if 1 <= share.x <= 100: role = 0
        elif 101 <= share.x <= 300: role = 1
        else: role = 2

        if not verify_token_hash(t_hash):
            insert_recover_log(uid=share.x, role_level=role, token_hash=t_hash, algorithm="RBAC", status="FAILED_INVALID_TOKEN")
            raise HTTPException(status_code=403, detail=f"Access Denied: Unrecognized token for ID {share.x}")
        
        valid_tokens.append({"uid": share.x, "role": role, "hash": t_hash, "y": share.y})

    submitted_ids = [vt["uid"] for vt in valid_tokens]
    count_b = sum(1 for x in submitted_ids if 1 <= x <= 100)    
    count_m = sum(1 for x in submitted_ids if 101 <= x <= 300)  
    count_e = sum(1 for x in submitted_ids if x > 300)          
    
    authorized = False
    error_msg = ""

    if count_e > 0:
        if (count_b + count_m) >= 2: authorized = True
        else: error_msg = "Denied: Need at least 2 supervisors."
    elif count_m > 0:
        if count_b >= 1: authorized = True
        else: error_msg = "Denied: Manager requires at least 1 Boss as backup."
    elif count_b > 0:
        if count_b >= 2: authorized = True
        else: error_msg = "Denied: At least 2 Boss required."
    else:
        error_msg = "Denied: Invalid token."

    if not authorized:
        for vt in valid_tokens:
            insert_recover_log(uid=vt["uid"], role_level=vt["role"], token_hash=vt["hash"], algorithm="RBAC", status="FAILED_RBAC_REJECTED")
        raise HTTPException(status_code=403, detail=error_msg)

    try:
        shares_tuple = [(vt["uid"], int(vt["y"])) for vt in valid_tokens]
        recovered_secret = recover_secret(shares_tuple)
        
        for vt in valid_tokens:
            insert_recover_log(uid=vt["uid"], role_level=vt["role"], token_hash=vt["hash"], algorithm="RBAC", status="SUCCESS")
            
        return RecoverResponse(message="Rahasia berhasil dipulihkan", secret=recovered_secret)
    except ValueError as e:
        for vt in valid_tokens:
            insert_recover_log(uid=vt["uid"], role_level=vt["role"], token_hash=vt["hash"], algorithm="RBAC", status="FAILED_MATH")
        raise HTTPException(status_code=403, detail=str(e))


# --- WEIGHTED SSS ---

@router.post("/split-weighted")
def split_weighted_endpoint(req: WeightedSplitRequest):
    try:
        shares_data = split_secret_weighted(req.secret, req.k, req.user_weights)
        formatted_response = {}
        
        for uid_str, shares_list in shares_data.items():
            uid = int(uid_str)
            weight = req.user_weights.get(uid_str, 0)
            formatted_response[uid_str] = []
            
            for s in shares_list:
                token_string = str(s[1])
                t_hash = hash_token(token_string)
                
                insert_split_log(uid=uid, role_level=weight, token_hash=t_hash, algorithm="WEIGHTED", status="SUCCESS")
                formatted_response[uid_str].append({"x": s[0], "y": token_string})
            
        return {"message": "Rahasia berhasil dipecah.", "k_required": req.k, "shares_by_user": formatted_response}
    except Exception:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")

@router.post("/recover-weighted")
def recover_weighted_endpoint(req: WeightedRecoverRequest):
    try:
        list_of_user_shares = []
        valid_tokens = []
        
        for uid_str, shares_list in req.submitted_shares.items():
            uid = int(uid_str)
            user_tuples = []
            
            for s in shares_list:
                t_hash = hash_token(s.y)
                if not verify_token_hash(t_hash):
                    insert_recover_log(uid=uid, role_level=0, token_hash=t_hash, algorithm="WEIGHTED", status="FAILED_INVALID_TOKEN")
                    raise HTTPException(status_code=403, detail=f"Access Denied: Unrecognized token for UID {uid}")
                
                valid_tokens.append({"uid": uid, "hash": t_hash})
                user_tuples.append((s.x, int(s.y)))
                
            list_of_user_shares.append(user_tuples)
            
        try:
            recovered_secret = recover_secret_weighted(list_of_user_shares)
            for vt in valid_tokens:
                insert_recover_log(uid=vt["uid"], role_level=0, token_hash=vt["hash"], algorithm="WEIGHTED", status="SUCCESS")
                
            return {"message": "Brankas Utama Berhasil Dibuka!", "secret": recovered_secret}
        except ValueError as math_err:
            for vt in valid_tokens:
                insert_recover_log(uid=vt["uid"], role_level=0, token_hash=vt["hash"], algorithm="WEIGHTED", status="FAILED_MATH")
            raise ValueError(math_err)

    except ValueError as e:
        raise HTTPException(status_code=403, detail=f"Denied: {str(e)}")


# --- TASSA (BIRKHOFF INTERPOLATION) ---

@router.post("/split-tassa")
def split_tassa_endpoint(req: TassaSplitRequest):
    try:
        shares_data = split_secret_tassa(req.secret, req.k, req.user_roles)
        formatted_shares = []
        
        for s in shares_data:
            token_string = str(s["y"])
            t_hash = hash_token(token_string)
            
            insert_split_log(uid=s["uid"], role_level=s["level"], token_hash=t_hash, algorithm="TASSA", status="SUCCESS")
            formatted_shares.append(TassaShareItem(uid=s["uid"], level=s["level"], y=token_string))
            
        return {"message": "Rahasia berhasil dipecah (Birkhoff).", "k_matrix_dim": req.k, "shares": formatted_shares}
    except Exception:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")

@router.post("/recover-tassa")
def recover_tassa_endpoint(req: TassaRecoverRequest):
    try:
        formatted_input = []
        
        for s in req.submitted_shares:
            t_hash = hash_token(s.y)
            if not verify_token_hash(t_hash):
                insert_recover_log(uid=s.uid, role_level=s.level, token_hash=t_hash, algorithm="TASSA", status="FAILED_INVALID_TOKEN")
                raise HTTPException(status_code=403, detail=f"Access Denied: Unrecognized token for UID {s.uid}")
            
            formatted_input.append({"uid": s.uid, "level": s.level, "y": int(s.y), "t_hash": t_hash})
        
        k_dim = len(formatted_input)
        
        try:
            recovered_secret = recover_secret_tassa(k_dim, formatted_input)
            for item in formatted_input:
                insert_recover_log(uid=item["uid"], role_level=item["level"], token_hash=item["t_hash"], algorithm="TASSA", status="SUCCESS")
                
            return {"message": "Matriks Birkhoff Berhasil Dipecahkan!", "secret": recovered_secret}
        except ValueError as math_err:
            for item in formatted_input:
                insert_recover_log(uid=item["uid"], role_level=item["level"], token_hash=item["t_hash"], algorithm="TASSA", status="FAILED_MATRIX_REJECTED")
            raise ValueError(math_err)

    except ValueError as e:
        raise HTTPException(status_code=403, detail=f"Denied: {str(e)}")