from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes.readings import router as readings_router
from routes.progress import router as progress_router

app = FastAPI()


app.include_router(readings_router)
app.include_router(progress_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

@app.get("/you_there")
def read_you_there():
    return {"status": "👍"}