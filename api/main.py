from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_core import router as core_router
from api.routes_github import router as github_router

app = FastAPI(
    title="Codeparser API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router)
app.include_router(github_router)


@app.get("/")
def root():
    return {"message": "API is running"}
