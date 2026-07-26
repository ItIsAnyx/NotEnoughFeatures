from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

class DataReader(BaseModel):
    source: str
    filename: str
    filetype: str
    size: str

router = APIRouter(prefix="/data_readers")

async def read_pdf(file: UploadFile):
    try:
        return await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/read_file", response_model=DataReader)
async def read_file_endpoint(filetype: str, source: str = "/data_readers/read_file", file: UploadFile = File(...)):
    if filetype == "pdf":
        await read_pdf(file)
    else:
        raise HTTPException(status_code=400, detail="File type not supported")

    return {
        "source": source,
        "filename": file.filename,
        "filetype": filetype,
        "size": f"{file.size} bytes"
    }