from fastapi import APIRouter
from src.services.retrain_service import auto_retrain

router=APIRouter()

router.post('/retrain')
def retraiin_models():
    auto_retrain()
    return {'status':'Retraining Complete'}
