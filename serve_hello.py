from fastapi import FastAPI
import ray
from ray import serve
import os
from fp import FastAPIInstrumentor

import requests
import time



# Use this var to test service inplace update. When the env var is updated, users see new return value.
msg = os.getenv("SERVE_RESPONSE_MESSAGE", "Hello world!")

app = FastAPI()
FastAPIInstrumentor().instrument_app(app)


@serve.deployment(route_prefix="/", num_replicas=2)
@serve.ingress(app)
class HelloWorld:
    @app.get("/")
    def hello(self):
        return msg

    @app.get("/healthcheck")
    def healthcheck(self):
        return

    @app.options("/")
    def hello2(self):
        return "hellllooo"



entrypoint = HelloWorld.bind()


# The following block will be executed if the script is run by Python directly
if __name__ == "__main__":

    serve.run(entrypoint)

    for i in range(5):
        response = requests.get("http://127.0.0.1:8000/")
        time.sleep(1)