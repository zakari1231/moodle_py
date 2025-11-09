from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
import pandas as pd
from fpdf import FPDF
import io
import os

app = FastAPI(title="GTU Student Credential API")

DATA_PATH = "data.csv"

def load_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("data.csv file not found.")
    return pd.read_csv(DATA_PATH)

def find_student(firstname: str, lastname: str, num_inscreption: str):
    data = load_data()
    match = data[
        (data["firstname"].str.lower().str.strip() == firstname.lower().strip()) &
        (data["lastname"].str.lower().str.strip() == lastname.lower().strip()) &
        (data["num_inscreption"].astype(str).str.strip() == str(num_inscreption).strip())
    ]
    return match