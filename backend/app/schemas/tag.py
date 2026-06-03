from pydantic import BaseModel


class TagOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
