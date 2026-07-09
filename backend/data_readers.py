from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

class DataReader(BaseModel):
    source: str
    data: str

router = APIRouter(prefix="/data_readers")

async def read_pdf(file: UploadFile):
    return await file.read()

@router.post("/read_file", response_model=DataReader)
async def read_file_endpoint(source: str, filetype: str, file: UploadFile = File(None)):
    if filetype == "pdf":
        data = await read_pdf(file)
    else:
        raise HTTPException(status_code=400, detail="File type not supported")

    return {
        "source": source,
        "data": data
    }