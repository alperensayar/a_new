
from pydantic import BaseModel
from typing import List

class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    refresh_token: str

class TokenData(BaseModel):
    email: str = None
    company_id: str = None

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    company_id: str
class UserAuth(BaseModel):
    email: str
    password: str

class SurveySend(BaseModel):
    receiver_name: str
    receiver_email: str
    survey_id: str
    sending_time: str
    language: str
    dep: str

class SurveyToken(BaseModel):
    token: str

class ChangePassword(BaseModel):
    receiver_email: str
    receiver_pass1:str
    receiver_pass2:str
class Result(BaseModel):
    name: str
    email: str
    department: str
    survey_name: str
    sending_date: str
    finished_date: str
    pdf: str