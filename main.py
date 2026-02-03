from fastapi import FastAPI
import uvicorn
from routers.moderation import router as moderation_router

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


app.include_router(moderation_router, prefix='/moderation')

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8003)
