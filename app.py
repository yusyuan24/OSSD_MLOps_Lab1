from fastapi import FastAPI
from pydantic import BaseModel
import joblib
 
app = FastAPI()
model = joblib.load("model.pkl")
 
class Req(BaseModel):
    instances: list[list[float]]
 
@app.post("/predict")
def predict(req: Req):
    y = model.predict(req.instances)
    return {"predictions": y.tolist()}
 
@app.get("/healthz")
def healthz():
    return {"ok": True}
