from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path

from routes.login import auth_router
from routes.project import project_router
from routes.comparison import compare_router

from utils import UPLOAD_FOLDER, RESULT_FOLDER

# SETUP APP
app = FastAPI(title="Visual Testing API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(project_router, tags=["Projects"])
app.include_router(compare_router, tags=["Image Comparison"])

@app.get("/")
async def root():
    return {"message": "Visual Testing API", "version": "2.0.0", "storage": "cloudinary"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)