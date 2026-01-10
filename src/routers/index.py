from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/index")
async def index_file(request: Request):
    # receive file

    # create a id and a process to read chunk by chunk and store embeddings

    # return id for user to check process
    pass

@router.get("/status/{id}")
async def get_status(id: str):
    # get status of process with id

    # return status
    pass
