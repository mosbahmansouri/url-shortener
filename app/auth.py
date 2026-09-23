import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

secret = os.environ.get("JWT_SECRET")

if not secret: 
    raise RuntimeError("JWT secret key not found in environment variables")

algorithm = "HS256"
expire_minutes = 30
security = HTTPBearer()

def create_token(user_id:int ) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),

    }
    return jwt.encode(payload, secret, algorithm=algorithm)



def get_current_user_id(creds: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(creds.credentials, secret, algorithms=[algorithm])
        return int(payload.get("sub"))

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")    









