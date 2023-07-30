# main.py
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

Base.metadata.create_all(bind=engine)

app = FastAPI()

class ContactBase(BaseModel):
    name: str
    surname: str
    email: str
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None

class Contact(ContactBase):
    id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/contacts/", response_model=Contact)
def create_contact(contact: ContactBase, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts/", response_model=List[Contact])
def get_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Contact).offset(skip).limit(limit).all()

@app.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: int, updated_contact: ContactBase, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in updated_contact.dict().items():
        setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact

@app.delete("/contacts/{contact_id}", response_model=Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return contact

@app.get("/search/", response_model=List[Contact])
def search_contacts(query: str = Query(None, min_length=3), db: Session = Depends(get_db)):
    if query is None:
        return []
    return db.query(Contact).filter(
        (Contact.name.ilike(f"%{query}%"))
        | (Contact.surname.ilike(f"%{query}%"))
        | (Contact.email.ilike(f"%{query}%"))
    ).all()

@app.get("/birthdays/", response_model=List[Contact])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=7)
    return db.query(Contact).filter(Contact.birthday.between(start_date, end_date)).all()
