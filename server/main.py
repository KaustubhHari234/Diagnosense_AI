from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.auth.route import router as auth_router
from server.reports.route import router as report_router
from server.diagnosis.route import router as diagnosis_router


app=FastAPI(title="MedicalDiagnosis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router)
print("Auth router included")
app.include_router(report_router)
app.include_router(diagnosis_router)