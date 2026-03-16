from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from src.server.storage import Storage, PathTraversalError

def make_router(storage: Storage) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @router.put("/files/{path:path}")
    async def upload_file(path: str, request: Request) -> dict:
        try:
            data = await request.body()
            storage.write(path, data)
        except PathTraversalError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"path": path, "bytes": len(data)}
    
    @router.delete("/files/{path:path}")
    async def delete_file(path: str) -> dict:
        try:
            if not storage.exists(path):
                raise HTTPException(status_code=404, detail="File not found")
            storage.delete(path)
        except PathTraversalError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"deleted": path}
    
    @router.get("/files/{path:path}")
    async def download_file(path: str) -> Response:
        try:
            if not storage.exists(path):
                raise HTTPException(status_code=404, detail="File not found")
            data = storage.read(path)
        except PathTraversalError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return Response(content=data, media_type="application/octet-stream")
    
    return router