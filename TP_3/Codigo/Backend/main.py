from fastapi import FastAPI

app = FastAPI()


@app.get("/resultados")
def get_resultados():
    return {"message": "Resultados endpoint"}
