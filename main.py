from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(
    title="LegalEase API",
    description="AI-powered legal document draft generator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "app": "LegalEase",
        "status": "running",
        "docs": "/docs",
        "generate": "/generate",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
