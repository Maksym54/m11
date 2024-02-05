import app
from django.conf.global_settings import SECRET_KEY
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import Contact
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_limiter import FastAPILimiter
from fastapi import Depends
from database import SessionLocal
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

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, index=True, unique=True)
    phone_number = Column(String)
    birthday = Column(DateTime)
    additional_data = Column(String, nullable=True)

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: datetime
    additional_data: str = None

class ContactUpdate(ContactCreate):
    pass

limiter = FastAPILimiter(key_func=get_user_email)
rate_limit = Depends(limiter)

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
    """
    Retrieve a list of contacts.
    """
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = FastAPILimiter(key_func=get_user_email)
rate_limit = Depends(limiter)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "https://frontendapp.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/contacts/", response_model=Contact)
def create_contact(contact: ContactCreate, db: SessionLocal = Depends(SessionLocal)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts/", response_model=list[Contact])
def read_contacts(query: str = Query(None)):
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

@app.get("/contacts/{contact_id}", response_model=Contact)
def read_contact(contact_id: int):
    db = SessionLocal()
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    db.close()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: int, contact: ContactUpdate):
    db = SessionLocal()
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        db.close()
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    db.close()
    return db_contact

@app.delete("/contacts/{contact_id}", response_model=Contact)
def delete_contact(contact_id: int):
    db = SessionLocal()
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        db.close()
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    db.close()
    return db_contact

@app.get("/contacts/birthday", response_model=list[Contact])
def get_contacts_upcoming_birthdays():
    db = SessionLocal()
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    contacts = (
        db.query(Contact)
        .filter((Contact.birthday >= today) & (Contact.birthday <= next_week))
        .all()
    )
    db.close()
    return contacts