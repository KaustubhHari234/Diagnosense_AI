from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .models import SignupRequest
from .hash_utils import hash_password, verify_password
from ..config.db import users_collection


router=APIRouter(prefix="/auth",tags=["auth"])
security=HTTPBasic()

print("Loaded auth router")


def authenticate(credentials:HTTPBasicCredentials=Depends(security)):
    user=users_collection.find_one({"username":credentials.username})
    if not user or not verify_password(credentials.password,user["password"]):
        raise HTTPException(status_code=401,detail="Invalid credentials")
    return {"username":user["username"],"role":user["role"]}

@router.post("/signup")
def signup(req:SignupRequest):
    if users_collection.find_one({"username":req.username}):
        raise HTTPException(status_code=400,detail="user already exists")
    users_collection.insert_one({
        "username":req.username,
        "password":hash_password(req.password),
        "role":req.role
    })
    return {"message":"User created successfully"}



@router.get("/login")
def login(user=Depends(authenticate)):
    return {"username":user["username"],"role":user["role"]}