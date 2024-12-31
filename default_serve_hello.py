from fastapi import FastAPI
from ray import serve

app = FastAPI()

@serve.deployment
@serve.ingress(app)
class HelloWorld:
    @app.get("/")
    def hello(self):
        return "Hello world!"

app = HelloWorld.bind()
