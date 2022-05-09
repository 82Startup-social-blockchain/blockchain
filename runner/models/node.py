
from pydantic import BaseModel


class NodeAddress(BaseModel):
    address: str
