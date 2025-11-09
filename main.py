from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
import pandas as pd
from fpdf import FPDF
import io
import os

app = FastAPI(title="GTU Student Credential API")

DATA_PATH = "data.csv"