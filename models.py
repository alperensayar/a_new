
from sqlalchemy import Column, String, Integer, ForeignKey,DateTime,Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    users = relationship("User", back_populates="company")

class User(Base):
    __tablename__ = "users"
    name = Column(String)
    email = Column(String, primary_key=True)
    password = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="users")

class SurveySender(Base):
    __tablename__ = "survey_sender"

    id = Column(Integer, primary_key=True)
    receiver_name = Column(String)
    receiver_email = Column(String)
    new_token = Column(String)
    survey_id = Column(String)
    is_active = Column(Boolean,default=True)
    sender_id = Column(String)
    sending_time = Column(DateTime)
    language = Column(String)
    dep = Column(String)
class SurveyAnswer(Base):
    __tablename__ = 'survey_answer'
    id = Column(Integer, primary_key=True)
    token = Column(String)
    answers = Column(String)
    answers_time = Column(String)
class SResult(Base):
    __tablename__ = "tableData"
    id = Column(Integer, primary_key=True)
    name=Column(String)
    email=Column(String)
    department=Column(String)
    survey_name = Column(String)
    sending_date = Column(String)
    finished_date = Column(String)
    pdf = Column(String)


engine = create_engine("postgresql://postgres:postgres@localhost:5432/postgres")
Base.metadata.create_all(bind=engine)





