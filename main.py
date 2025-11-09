from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from fpdf import FPDF
import io
import os

app = FastAPI(title="GTU Student Credential API")

DATA_PATH = "data.csv"
_templates = Jinja2Templates(directory="templates")

# --- Load CSV once (simple cache) ---
_data_cache = None
def load_data():
    global _data_cache
    if _data_cache is not None:
        return _data_cache
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"{DATA_PATH} file not found.")
    df = pd.read_csv(DATA_PATH, dtype=str).fillna("")
    # normalize columns names if necessary
    df.columns = [c.strip() for c in df.columns]
    _data_cache = df
    return _data_cache

def find_student(firstname: str, lastname: str, num_inscreption: str):
    df = load_data()
    cond = (
        (df["firstname"].str.lower().str.strip() == firstname.lower().strip()) &
        (df["lastname"].str.lower().str.strip() == lastname.lower().strip()) &
        (df["num_inscreption"].astype(str).str.strip() == str(num_inscreption).strip())
    )
    result = df[cond]
    return result

# --- Serve the HTML page ---
@app.get("/")
def index(request: Request):
    return _templates.TemplateResponse("index.html", {"request": request})

# --- API endpoint: JSON response ---
@app.get("/get_credentials/")
def get_credentials(
    firstname: str = Query(..., description="First name"),
    lastname: str = Query(..., description="Last name"),
    num_inscreption: str = Query(..., description="Registration number")
):
    match = find_student(firstname, lastname, num_inscreption)
    if match.empty:
        return JSONResponse(status_code=404, content={"error": "Information not correct or student not registered at GTU."})
    record = match.iloc[0].to_dict()
    # return only selected fields (avoid extra pandas metadata)
    response = {
        "firstname": record.get("firstname",""),
        "lastname": record.get("lastname",""),
        "num_inscreption": record.get("num_inscreption",""),
        "username": record.get("username",""),
        "password": record.get("password","")
    }
    return JSONResponse(content=response)

# --- API endpoint: returns PDF (stream) ---
@app.get("/get_credentials_pdf/")
def get_credentials_pdf(
    firstname: str = Query(...),
    lastname: str = Query(...),
    num_inscreption: str = Query(...)
):
    match = find_student(firstname, lastname, num_inscreption)
    if match.empty:
        raise HTTPException(status_code=404, detail="Student not found or incorrect information.")
    record = match.iloc[0].to_dict()

    # Create PDF in memory
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "GTU Student Credentials", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", size=12)
    lines = [
        f"First name: {record.get('firstname','')}",
        f"Last name: {record.get('lastname','')}",
        f"Registration #: {record.get('num_inscreption','')}",
        f"Username: {record.get('username','')}",
        f"Password: {record.get('password','')}",
    ]
    for line in lines:
        pdf.cell(0, 8, txt=line, ln=True)

    # ✅ Correct way to get PDF bytes
    pdf_bytes = io.BytesIO(pdf.output(dest="S").encode("latin1"))

    filename = f"{record.get('firstname','user')}_{record.get('lastname','user')}_credentials.pdf"
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# If you later want to serve static files (css/js), mount a static folder:
# app.mount("/static", StaticFiles(directory="static"), name="static")
