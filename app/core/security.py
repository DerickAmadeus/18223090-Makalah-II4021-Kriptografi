import hashlib

def hash_token(token_value: str) -> str:
    return hashlib.sha256(str(token_value).encode('utf-8')).hexdigest()