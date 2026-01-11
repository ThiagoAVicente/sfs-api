from fastapi import HTTPException

def required(v, t):
    if not v:
        raise HTTPException(status_code=400, detail=f"{t} required")
