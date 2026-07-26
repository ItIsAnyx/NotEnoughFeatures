from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import pymupdf4llm
import pymupdf

class BasicFileTransformer(BaseModel):
    source: str
    data: str
    is_saved: bool
    save_path: str

router = APIRouter(prefix="/data_transformers")

def pdf_to_md(pdf_bytes: bytes):
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return pymupdf4llm.to_markdown(doc)

@router.post("/pdf_to_md", response_model=BasicFileTransformer)
async def pdf_to_md_endpoint(save_path: str = "", source: str = "/data_transformers/pdf_to_md", file: UploadFile = File(None)):
    pdf_bytes = await file.read()
    data = pdf_to_md(pdf_bytes)
    print(data)
    is_saved = False

    if save_path != "":
        if not(save_path.endswith(".md")):
            save_path += ".md"

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(data)
        is_saved = True

    return {
        "source": source,
        "data": data,
        "is_saved": is_saved,
        "save_path": save_path
    }