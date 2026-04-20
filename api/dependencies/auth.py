"""
dependencies/auth.py
--------------------
API key authentication dependency.

Reads X_API_KEY from .env and validates the x-api-key request header.
"""

import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()

_API_KEY = os.getenv("X_API_KEY")


def require_api_key(x_api_key: str = Header(..., description="API key for protected endpoints")):
    if not _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="X_API_KEY is not configured on the server",
        )
    if x_api_key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
