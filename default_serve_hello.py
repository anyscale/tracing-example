from fastapi import FastAPI
from ray import serve
import os

app = FastAPI()

@serve.deployment(route_prefix="/")
@serve.ingress(app)
class HelloWorld:
    @app.get("/")
    def hello(self):
        return "Hello world!"

app = HelloWorld.bind()