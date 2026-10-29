from fastapi import APIRouter
from app.api.v1.endpoints import vulnerabilities, indicators

api_router = APIRouter()
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["IoC Indicators"])