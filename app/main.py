from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI with uv!"}



@app.get("/health")
def get_health_status():
    return {"message": "Service is healthy!"}