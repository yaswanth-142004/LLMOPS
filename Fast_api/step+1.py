from unittest.util import _MAX_LENGTH
from fastapi import FastAPI ,Query , Path
from typing import Annotated 
from pydantic import BaseModel , AfterValidator 

app = FastAPI()


def check_valid_q(id:str):
    if not id.startswith("q"):
        raise ValueError("Invalid format")
    
    
@app.get("/items/{item_id}")
async def read_items(
    
    item_id:Annotated[int,Path(title)]
    q:Annotated[str|None ,AfterValidator(check_valid_q),Query(
    
                                                    max_length=50,
                                                    alias="item-query",
                                                    title="Query-string",
                                                    description="Query string for the items to search in the database that have a good match",
                                                    min_length=3,
                                                    
                                                    
                                                    )] = None):
    results = {"items":[{"item_id":"Foo"}]}
    if q:
        results.update({"q":q})
        
    return results

