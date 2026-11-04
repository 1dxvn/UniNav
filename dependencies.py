from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from security.authentication import get_current_user

DatabaseSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
