"""

Legal text responses.
Frontend can just render the returned string.
"""

from pydantic import BaseModel


class LegalTextOut(BaseModel):
    text: str
