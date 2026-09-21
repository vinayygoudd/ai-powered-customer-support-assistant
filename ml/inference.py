from app.services.ml_service import MLPredictor

def predict(message, model_dir="models"):
    return MLPredictor(model_dir).predict(message)
