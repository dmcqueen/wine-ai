#!/usr/bin/env python3

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class TextRequest(BaseModel):
    text: str


app = FastAPI()


@app.post("/")
async def get_embedding(request_data: TextRequest):
    text = request_data.text
    if not text:
        raise HTTPException(status_code=400, detail="can't get text")

    embedding = model.encode(text).tolist()

    return {"paraphrase-multilingual-MiniLM-L12-v2": embedding}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8088)
