from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes.login import auth_router
from routes.project import project_router
from routes.comparison import compare_router

app = FastAPI(title="Visual Testing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(project_router)
app.include_router(compare_router)

@app.get("/")
async def root():
    return {"message": "Visual Testing API", "storage": "cloudinary"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)