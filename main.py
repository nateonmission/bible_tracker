from fastapi import FastAPI
from routes.readings import router as readings_router
from routes.progress import router as progress_router

app = FastAPI()


app.include_router(readings_router)
app.include_router(progress_router)


@app.get("/you_there")
def read_you_there():
    return {"status": "👍"}