from pydantic import BaseModel, Field

class FetchDB(BaseModel):
    mongodb_query: str = Field(description="The mongodb query to fetch the data from the collection, output should always contain **collection.** followed by the relevant condition")

