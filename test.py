from fastapi import FastAPI #
from h11 import Request
import uvicorn

app = FastAPI()

@app.post("/")              #
def any_route(query: str):            #
  print(query)
  return {}


if __name__ == "__main__":
  uvicorn.run("test:app", reload=True)