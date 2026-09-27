import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import datetime
import requests
import re
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="AppIDE & Admin Portal", layout="wide")

# ==========================================
# ΚΕΝΤΡΙΚΗ ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS (ΥΠΟΣΤΗΡΙΞΗ ΟΛΩΝ ΤΩΝ SECRETS)
# ==========================================
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_dict = {}
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
    elif "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    else:
        # Fallback τοπικό αρχείο αν υπάρχει
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        return gspread.authorize(creds)
        
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@st.cache_resource
def get_products_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_products")
