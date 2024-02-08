from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import Contact
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_limiter import FastAPILimiter
from fastapi import Depends
from database import SessionLocal
from main import ContactCreate
from models import User
from auto import get_user_email

SECRET_KEY = "123654"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_jwt_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception

DATABASE_URL = "postgresql://username:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Contact(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: datetime
    additional_data: str = None

class ContactUpdate(Contact):
    pass

limiter = FastAPILimiter(key_func=get_user_email)
rate_limit = Depends(limiter)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/contacts/", response_model=Contact, dependencies=[rate_limit])
def create_contact(
    contact: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(SessionLocal),
):
    db_contact = Contact(**contact.dict(), user_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts/", response_model=list[Contact], summary="Get list of contacts", dependencies=[Depends(rate_limit)])
def read_contacts(query: str = Query(None, description="Search by name, last name, or email")):
    db = SessionLocal()
    contacts = db.query(Contact)
    if query:
        contacts = contacts.filter(
            (Contact.first_name.ilike(f"%{query}%"))
            | (Contact.last_name.ilike(f"%{query}%"))
            | (Contact.email.ilike(f"%{query}%"))
        )
    db.close()
    return contacts.all()