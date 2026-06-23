"""Simple HTTP Basic Auth — same pattern as OrdeRR."""
import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    username = os.getenv("DASHBOARD_USERNAME", "admin")
    password = os.getenv("DASHBOARD_PASSWORD", "changeme")
    ok = (
        secrets.compare_digest(credentials.username.encode(), username.encode())
        and secrets.compare_digest(credentials.password.encode(), password.encode())
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
