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

@app.get("/get_credentials/")
def get_credentials(
    firstname: str = Query(..., description="Student first name"),
    lastname: str = Query(..., description="Student last name"),
    num_inscreption: str = Query(..., description="Student registration number")
):
    """Return student credentials in JSON format (for web integration)."""
    match = find_student(firstname, lastname, num_inscreption)

    if match.empty:
        return JSONResponse(
            status_code=404,
            content={"error": "Information not correct or student not registered at GTU."}
        )

    record = match.iloc[0].to_dict()
    return JSONResponse(content=record)

@app.get("/get_credentials_pdf/")
def get_credentials_pdf(
    firstname: str = Query(...),
    lastname: str = Query(...),
    num_inscreption: str = Query(...)
):
    """Return student credentials as a downloadable PDF."""
    match = find_student(firstname, lastname, num_inscreption)

    if match.empty:
        raise HTTPException(status_code=404, detail="Student not found or incorrect information.")

    record = match.iloc[0].to_dict()

    # Generate PDF in memory
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="GTU Student Credentials", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for key, value in record.items():
        pdf.cell(200, 10, txt=f"{key.capitalize()}: {value}", ln=True)

    # Write to BytesIO (no temp file)
    pdf_bytes = io.BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)

    return FileResponse(
        path_or_file=pdf_bytes,
        media_type="application/pdf",
        filename=f"{record['firstname']}_{record['lastname']}_credentials.pdf"
    )