from fastapi import APIRouter
from app.api.routes import health, accounts, acquisition, pipeline, predictions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(accounts.router)
api_router.include_router(acquisition.router)
api_router.include_router(pipeline.router)
api_router.include_router(predictions.router)

