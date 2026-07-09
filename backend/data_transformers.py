from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import pymupdf4llm
import pymupdf

class BasicFileTransformer(BaseModel):
    source: str
    data: str

router = APIRouter(prefix="/data_transformers")

def pdf_to_md(pdf_bytes: bytes):
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return pymupdf4llm.to_markdown(doc)

@router.post("/pdf_to_md", response_model=BasicFileTransformer)
async def pdf_to_md_endpoint(source, file: UploadFile = File(None)):
    pdf_bytes = await file.read()
    return {
        "source": source,
        "data": pdf_to_md(pdf_bytes)
    }