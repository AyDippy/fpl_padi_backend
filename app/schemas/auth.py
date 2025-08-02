from pydantic import BaseModel

class Token(BaseModel):
    """
    Represents a JWT token.
    
    This model is used to return the JWT token in the authentication response.
    """
    access_token: str
    token_type: str = "bearer"