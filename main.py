from fastapi import FastAPI
from routes.readings import router as readings_router

app = FastAPI()


app.include_router(readings_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/you_there")
def read_you_there():
    return {"status": "👍"}