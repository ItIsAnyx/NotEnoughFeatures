from fastapi import FastAPI, UploadFile, File
from config import settings
from data_readers import router as data_reader
from data_transformers import router as data_transformer

from data_readers import read_pdf
from data_transformers import pdf_to_md

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.include_router(data_reader)
app.include_router(data_transformer)

@app.on_event("startup")
async def startup():
    print(f"{settings.APP_NAME} startup")

@app.post("/example/pdf_md_tg-pipeline")
async def example_pdf_md_tg_pipeline(usertag: str, file: UploadFile = File(...)):
    pdf_bytes = await read_pdf(file)
    md_doc = pdf_to_md(pdf_bytes)
    # send_message = await tg_send_message(...)
    return {"usertag": usertag, "markdown": md_doc}