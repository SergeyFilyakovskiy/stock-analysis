from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    root_path='/auth-service',
    version='0.1.0',
    title='Authentication Service',
)

Instrumentator().instrument(app).expose(app)

@app.get('/')
async def health():
    return {'status':'health'}