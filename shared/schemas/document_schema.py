from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: int
    file_name: str
    status: str

    class Config:
        from_attributes = True
