from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any
import uvicorn

from invoice_qc import validator

app = FastAPI(title="Invoice QC API", version="0.1")

class Invoice(BaseModel):
   
    __root__: Any

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/validate-json")
def validate_json(payload: List[dict]):
 
    try:
        results = validator.validate_invoices(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {e}")
    return results


@app.post("/validate")
def validate_body(payload: Any):
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise HTTPException(status_code=400, detail="Expecting a list of invoices or a single invoice dict.")
    return validator.validate_invoices(payload)

if __name__ == "__main__":
    uvicorn.run("invoice_qc.api:app", host="127.0.0.1", port=8000, reload=True)
