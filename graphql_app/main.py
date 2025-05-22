from fastapi import FastAPI, Request
from strawberry.fastapi import GraphQLRouter
from .schema import schema

app = FastAPI(title="Spatial Data Platform GraphQL API")

graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql") 