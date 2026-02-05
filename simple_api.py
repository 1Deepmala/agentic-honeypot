from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/")
async def root_post():
    return JSONResponse({"status": "success", "reply": "Hello from honeypot"})

@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)