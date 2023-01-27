
from fastapi import FastAPI, HTTPException, Depends,Response,Header
import requests
from security import create_access_token, create_refresh_token, validate_token, get_current_user, oauth2_scheme,verify_password,hash_password,create_token
from models import User, SurveySender,SurveyAnswer,SResult
from schemas import UserCreate,Token,TokenData,UserAuth,SurveySend,SurveyToken,ChangePassword,Result
from database import get_db
from sqlalchemy.orm import Session
import time
from fastapi.middleware.cors import CORSMiddleware



origins = {
    "http://localhost",
    "http://localhost:3000",
}
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/surveys")
def read_surveys(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    surveys = db.query(SResult).offset(skip).limit(limit).all()
    print(surveys)
    return surveys
@app.post("/login", response_model=Token,status_code=200)
async def login(user: UserAuth, db:Session=Depends(get_db),response:Response=Response):
    user_obj = db.query(User).filter_by(email=user.email).first()
    if not user_obj:
        response.status_code = 404
        return {"message": "Invalid email or password"}
    if not verify_password(user.password, user_obj.password):
        response.status_code = 404
    company_id = user_obj.company_id
    

    try:
        access_token = create_access_token({"sub": user_obj.email, "company_id": company_id})
        refresh_token = create_refresh_token({"sub": user_obj.email, "company_id": company_id})
        response.status_code = 200
        return {"access_token": access_token, "refresh_token": refresh_token}
    except Exception as e:
        response.status_code = 400
        return {"message": "Error logging in"}

@app.post("/signup",status_code=200)
async def signup(user: UserCreate, db:Session =Depends(get_db),response:Response=Response):
    user_obj = db.query(User).filter_by(email=user.email).first()
    if user_obj:
        response.status_code = 404
        return {"message": "Email already registered"}
    hashed_password = hash_password(user.password)
    try:
        new_user = User(email=user.email, password=hashed_password,company_id=user.company_id,name=user.name)
        db.add(new_user)
        db.commit()
        response.status_code = 201
        return {"message": "User created successfully"}
    except Exception as e:
        response.status_code = 400
        return {"message": "Error creating user"}

@app.get("/home")
async def home(current_user: TokenData = Depends(get_current_user)):
    """Home endpoint, requires login"""
    return {"message": "Welcome to the home page"}

@app.get("/token/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """Refresh an access token"""
    try:
        payload = validate_token(token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        # check if user exists in database
        user = User.query.filter_by(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        access_token = create_access_token({"sub": user.email, "company_id": user.company_id})
        return {"access_token": access_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token")

@app.post("/surveysender")
def send_survey(survey_data: SurveySend,db:Session = Depends(get_db),token: str = Depends(oauth2_scheme)):


    payload = validate_token(token)
    email = payload.get("sub")
    company_id = payload.get("company_id")
  
    new_token = create_token(company_id, survey_data.receiver_email, survey_data.survey_id, str(survey_data.sending_time), survey_data.language)
    survey_sending = SurveySender(
        receiver_name=survey_data.receiver_name,
        receiver_email=survey_data.receiver_email,
        survey_id=survey_data.survey_id,
        sending_time=str(survey_data.sending_time),
        new_token=new_token,
        sender_id=company_id,
        language=survey_data.language,
        dep=survey_data.dep
    )
    db.add(survey_sending)
    db.commit()

    return {"message": "Survey sent successfully"}

@app.post("/survey")
def render_survey(token_data: SurveyToken, db: Session = Depends(get_db)):
    try:
        payload = validate_token(token_data.token)
        survey_id = payload.get("survey_id")
        sending_time = payload.get("sending_time")
        language = payload.get("language")
        print(survey_id)
        survey_a = db.query(SurveySender).filter_by(survey_id=survey_id,sending_time=sending_time).first()

        if not survey_a:
            return {"is_valid": False}
        
        if  not survey_a.is_active:
            return {"is_valid": True, "is_completed": False, "survey_id": survey_id}
    except Exception as e:
        return {"is_valid": False}

    survey = db.query(SurveySender).filter(SurveySender.survey_id == survey_id, SurveySender.is_active == True).first()
    if not survey:
        return {"is_valid": False}
    return {"is_valid": True, "is_completed": survey.is_active, "survey_id": survey.survey_id, "language": language}


@app.post("/survey/submit")
async def handle_survey_submit(survey_data: dict,db:Session = Depends(get_db)):
    try:
        
        token = survey_data.get("token")
        time_r = survey_data.get("time")
        answers = survey_data.get("survey")
    
        payload = validate_token(token)
        survey_id = payload.get("survey_id")
        survey_a = db.query(SurveySender).filter_by(survey_id=survey_id).first()

        if not survey_a:
            return {"is_valid": False}
        # sqlalchemy update query to update is_active to False for the survey with survey_id 
        db.query(SurveySender).filter_by(survey_id=survey_id).update({"is_active": False})
        db.commit()

        survey_answers = SurveyAnswer(answers=str(answers), token=token, answers_time=str(time_r))
        db.add(survey_answers)
        db.commit()
        print(survey_answers)
        print(survey_a)
        db.refresh(survey_a)
        print("bitti")
        return {"status": "success", "message": "Survey submitted successfully."}
    except Exception as e:
        print(e)
        db.rollback()
        return {"status": "error", "message": "Error submitting survey."}

@app.post("/changepassword")
async def change_password(password_data: ChangePassword, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = validate_token(token)
        email = payload.get("sub")
        user = db.query(User).filter_by(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if (password_data.receiver_pass1!=password_data.receiver_pass1):
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        hashed_password = hash_password(user.password)
        db.query(User).filter_by(email=password_data.receiver_email).update({"password": hashed_password})
        db.commit()
        return {"message": "Password changed successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Error changing password")

# @app.post("/survey")
# def render_survey(token_data: SurveyToken, db: Session = Depends(get_db)):
#     try:
        
#         token = token_data.token
#         payload = validate_token(token)
#         survey_id2 = payload.get("survey_id")
        
#         #check if survey is active

#         survey_a = db.query(SurveySender).filter_by(survey_id=survey_id2).first()
      
      
#         if not survey_a:
#             raise HTTPException(status_code=400, detail="Invalid token")
#         is_active = survey_a.is_active
#         if not is_active:
#             raise HTTPException(status_code=400, detail="Survey is no longer active.")
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=400, detail="Invalid token")
    
#     # check if survey exists in the database
#     survey = db.query(SurveySender).filter(SurveySender.survey_id == survey_id2, SurveySender.is_active == True).first()
#     if not survey:
#         raise HTTPException(status_code=404, detail="Survey not found")
    
#     # return the appropriate survey page based on the survey_id
#     if survey_id2 == "Survey 1":
#         return survey_id2
#     elif survey_id2 == "Survey 2":
#         return survey_id2
#     elif survey_id2 == "Survey 3":
#         return survey_id2
