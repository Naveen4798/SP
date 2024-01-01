'''References
1) https://fastapi.tiangolo.com/
2) https://github.com/sumanentc/python-sample-FastAPI-application
3) https://dassum.medium.com/building-rest-apis-using-fastapi-sqlalchemy-uvicorn-8a163ccf3aa1
4) https://learning.postman.com/docs/writing-scripts/test-scripts/
5) https://gist.github.com/mikerj1/f10b152c80ddab693ef94fce2e033236
6) https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/api.html'''

import re
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a FastAPI app
app = FastAPI()


Base = declarative_base()

# Define the Person model for SQLAlchemy
class PersonDB(Base):
    __tablename__ = 'phonebook'
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    phone_number = Column(String)

# Configure the SQLite database engine
DATABASE_URL = "sqlite:///./phonebook.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)

# Create a Session class to handle database interactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Define a regular expression pattern for valid names
name_pattern = re.compile(r'^([A-Za-z]+(?:[\'\s][A-Za-z]+)?)(?:,\s([A-Za-z]+(?:[\'\s][A-Za-z]+)?)|,\s([A-Za-z]+(?:[\'\s][A-Za-z]+)?)(?:\s([A-Za-z]+(?:[\'\s][A-Za-z]+)?))?)?$')


# Define a regular expression pattern for valid phone numbers
phone_pattern = re.compile(r'^(\+\d{1,4}\s?)?(\(\d{1,}\)\s?)?(\d{1,}\s?[-.])?\d{1,}(\s?\d{1,}[-.])?\d{1,}(\s?\d{1,}(\s?[-.])?\d{1,})?$')


# Define an audit log file
audit_log_file = "audit.log"

# Configure the logger
logging.basicConfig(filename=audit_log_file, level=logging.INFO, format='%(asctime)s - %(message)s')


def is_valid_name(name):
    return bool(name_pattern.match(name))

def is_valid_phone_number(phone_number):
    return bool(phone_pattern.match(phone_number))

class Person(BaseModel):
    full_name: str
    phone_number: str



def check_contact_exists(name):
    session = SessionLocal()
    result = session.execute(select(PersonDB).where(PersonDB.full_name == name)).scalar()
    session.close()
    return result is not None


def check_contact_exists_by_phone(phone_number):
    session = SessionLocal()
    result = session.execute(select(PersonDB).where(PersonDB.phone_number == phone_number)).scalar()
    session.close()
    return result is not None



@app.post("/PhoneBook/add")
def add_person(person: Person):
    if not is_valid_name(person.full_name):
        raise HTTPException(status_code=400, detail="Invalid name format")
    if not is_valid_phone_number(person.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    if check_contact_exists(person.full_name):
        raise HTTPException(status_code=403, detail=f"error:' {person.full_name}' already exists in database.")
    if check_contact_exists_by_phone(person.phone_number):
        raise HTTPException(status_code=403, detail=f"error:' {person.phone_number}' already belongs to a contact. Please use a different number.")

    # Continue with adding the person to the phonebook
    session = SessionLocal()
    person_db = PersonDB(full_name=person.full_name, phone_number=person.phone_number)
    session.add(person_db)
    session.commit()
    session.close()
    logging.info(f"Added person: Name - {person.full_name}, Phone Number - {person.phone_number}")
    return {"message": "Contact added successfully"}   


@app.put("/PhoneBook/deleteByName")
def delete_by_name(full_name: str):
    session = SessionLocal()
    person = session.execute(select(PersonDB).where(PersonDB.full_name == full_name)).scalar()
    
    if person is None:
        session.close()
        raise HTTPException(status_code=404, detail=f"error: '{full_name}' not found in the database.")

    session.delete(person)
    session.commit()
    session.close()
    logging.info(f"deleted person: Name - {full_name}")

    return {"message": f"Contact '{full_name}' deleted successfully."}


@app.put("/PhoneBook/deleteByNumber")
def delete_by_number(phone_number: str):
    session = SessionLocal()
    person = session.execute(select(PersonDB).where(PersonDB.phone_number == phone_number)).scalar()

    if person is None:
        session.close()
        raise HTTPException(status_code=404, detail=f"Contact with phone number : '{phone_number}' not found in the database.")

    # Retrieve the name from the person object
    full_name = person.full_name

    session.delete(person)
    session.commit()
    session.close()
    logging.info(f"deleted contact: phone number - {phone_number} Name - {full_name} deleted successfully.")

    return {"message": f"Contact with phone number : '{phone_number}' (Name: {full_name}) deleted successfully."}


@app.get("/PhoneBook/list")
def list_phonebook():
    session = SessionLocal()
    result = session.execute(select(PersonDB.id, PersonDB.full_name, PersonDB.phone_number).order_by(PersonDB.id)).all()
    session.close()
    
    # Convert the result to a list of dictionaries
    phonebook_list = [{"id": row[0], "full_name": row[1], "phone_number": row[2]} for row in result]
    logging.info(f"viewed list of persons, Phone Numbers")
    return phonebook_list

if __name__ == "__main__":
    import uvicorn
    #uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)
