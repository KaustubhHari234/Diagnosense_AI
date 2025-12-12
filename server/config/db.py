from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
import os


load_dotenv()

MONGO_URI=os.getenv("MONGO_URI")
DB_NAME=os.getenv("DB_NAME","rbac-diagnosis")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db=client[DB_NAME]


users_collection=db["users"]
reports_collection=db["reports"]
diagnosis_collection=db["diagnosis_history"]

