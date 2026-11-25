from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from .esquema import esquema

app = FastAPI(title="Streaming - GraphQL (Python)")
app.include_router(GraphQLRouter(esquema), prefix="/graphql")


@app.get("/saude")
def saude():
    return {"status": "ok"}