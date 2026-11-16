import base64
import csv
from datetime import datetime
from ftplib import FTP
import io
import json
import os
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =====================================================================
# 1. Website Configuration
# =====================================================================
st.set_page_config(
    page_title="Professional Python for System Development",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 2. Hosting Storage Helper Functions (FTP Migration)
# =====================================================================
FTP_HOST = "sp162.mschosting.cloud"
FTP_USER = "tukangfx"
FTP_PASS = "Signtech2025!"
REMOTE_EVIDENCES_DIR = "httpdocs/Trainer"
REMOTE_WORKSHOP_DIR = "httpdocs/Workshop"
REMOTE_HTTPDOCS_DIR = "httpdocs"
CSV_FILENAME = "list_of_trainers.csv"
REGISTRATION_FILENAME = "registration.csv"


def append_trainer_to_ftp_csv(trainer_data, cv_file=None):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        for folder in REMOTE_EVIDENCES_DIR.split("/"):
            if folder:
                try:
                    ftp.cwd(folder)
                except Exception:
                    ftp.mkd(folder)
                    ftp.cwd(folder)

        if cv_file is not None:
            safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", cv_file.name)
            filename_to_store = (
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
            )
            ftp.storbinary(
                f"STOR {filename_to_store}", io.BytesIO(cv_file.getvalue())
            )

        existing_content = io.BytesIO()
        file_exists = False
        try:
            ftp.retrbinary(f"RETR {CSV_FILENAME}", existing_content.write)
            file_exists = True
        except Exception:
            file_exists = False

        existing_content.seek(0)
        raw_text = (
            existing_content.read().decode("utf-8", errors="ignore").strip()
        )

        fieldnames = [
            "Timestamp",
            "Full Name",
            "Phone / WhatsApp",
            "Email Address",
            "Location",
            "Occupation",
            "Areas of Expertise",
            "Certifications",
        ]

        out_buffer = io.StringIO()
        writer = csv.DictWriter(out_buffer, fieldnames=fieldnames)

        if not file_exists or not raw_text:
            writer.writeheader()
        else:
            out_buffer.write(raw_text + "\n")

        writer.writerow({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Full Name": trainer_data.get("full_name", ""),
            "Phone / WhatsApp": trainer_data.get("phone_number", ""),
            "Email Address": trainer_data.get("email", ""),
            "Location": trainer_data.get("location", ""),
            "Occupation": trainer_data.get("occupation", ""),
            "Areas of Expertise": trainer_data.get("expertise", ""),
            "Certifications": trainer_data.get("certifications", ""),
        })

        csv_bytes = io.BytesIO(out_buffer.getvalue().encode("utf-8"))
        ftp.storbinary(f"STOR {CSV_FILENAME}", csv_bytes)

        ftp.quit()
        return True, "Success"
    except Exception as e:
        return False, str(e)


def append_registration_to_ftp_csv(reg_data):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        # Navigasi ke folder httpdocs/Workshop
        for folder in REMOTE_WORKSHOP_DIR.split("/"):
            if folder:
                try:
                    ftp.cwd(folder)
                except Exception:
                    ftp.mkd(folder)
                    ftp.cwd(folder)

        existing_content = io.BytesIO()
        file_exists = False
        try:
            ftp.retrbinary(
                f"RETR {REGISTRATION_FILENAME}", existing_content.write
            )
            file_exists = True
        except Exception:
            file_exists = False

        existing_content.seek(0)
        raw_bytes = existing_content.read()

        # Semak jika fail sedia ada ialah fail Excel binari (bermula dengan 'PK')
        is_binary_excel = raw_bytes.startswith(b"PK")
        raw_text = (
            ""
            if is_binary_excel
            else raw_bytes.decode("utf-8", errors="ignore").strip()
        )

        fieldnames = [
            "Timestamp",
            "Full Name",
            "Identity Card / Passport Number",
            "Gender",
            "Phone / WhatsApp",
            "Email Address",
            "Mailing Address",
            "Company / Organisation",
            "Current Job Title / Role",
            "Selected Course / Workshop",
            "Academic Qualification",
            "Payment Method",
        ]

        out_buffer = io.StringIO()
        writer = csv.DictWriter(out_buffer, fieldnames=fieldnames)

        if not file_exists or not raw_text:
            writer.writeheader()
        else:
            out_buffer.write(raw_text + "\n")

        writer.writerow({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Full Name": reg_data.get("full_name", ""),
            "Identity Card / Passport Number": reg_data.get("ic_passport", ""),
            "Gender": reg_data.get("gender", ""),
            "Phone / WhatsApp": reg_data.get("phone", ""),
            "Email Address": reg_data.get("email", ""),
            "Mailing Address": reg_data.get("address", ""),
            "Company / Organisation": reg_data.get("company", ""),
            "Current Job Title / Role": reg_data.get("job_title", ""),
            "Selected Course / Workshop": reg_data.get("course", ""),
            "Academic Qualification": reg_data.get("academic_status", ""),
            "Payment Method": reg_data.get("payment_method", ""),
        })

        csv_bytes = io.BytesIO(out_buffer.getvalue().encode("utf-8"))
        ftp.storbinary(f"STOR {REGISTRATION_FILENAME}", csv_bytes)

        ftp.quit()
        return True, "Success"
    except Exception as e:
        return False, str(e)


def format_drive_url(url):
    if not isinstance(url, str):
        return ""
    clean_val = url.strip()
    if not clean_val or clean_val.lower() == "nan":
        return ""

    # Ekstrak File ID unik Google Drive
    drive_match = re.search(r"(?:file/d/|id=|/d/)([\w-]+)", clean_val)
    if drive_match:
        file_id = drive_match.group(1)
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1600"

    if re.match(r"^[\w-]{20,}$", clean_val):
        return f"https://drive.google.com/thumbnail?id={clean_val}&sz=w1600"

    return clean_val


def parse_transition_mode(raw_mode):
    mode = str(raw_mode).strip().lower()
    if "horizontal" in mode:
        return "horizontal-slide"
    elif "vertical" in mode:
        return "vertical-slide"
    elif "zoom" in mode:
        return "zoom-fade"
    elif "flip" in mode:
        return "flip"
    elif "wipe" in mode:
        return "wipe"
    return "fade"


# =====================================================================
# 3. Poster Links & Social Media Icons
# =====================================================================
header_sheet_id = "1ScYufcdP5kdmeFWwDdPlm8A4ugjZywuQS6TuQbEkHpM"
header_csv_url = (
    f"https://docs.google.com/spreadsheets/d/{header_sheet_id}/export?format=csv"
)
try:
    df_header = pd.read_csv(header_csv_url)
    HEADER_BANNER_URL = format_drive_url(df_header.iloc[0, 8])
    FOOTER_BANNER_URL = format_drive_url(df_header.iloc[1, 8])
except Exception:
    HEADER_BANNER_URL = ""
    FOOTER_BANNER_URL = ""

# =====================================================================
# Home Poster Loader (Sheet ID with 'id' & 'mode' columns)
# =====================================================================
poster_sheet_id = "1EIA20NXDHueSeIJ-rfAArHGWujbSjW0nBoEnnFjH0ws"
poster_csv_url = (
    f"https://docs.google.com/spreadsheets/d/{poster_sheet_id}/export?format=csv"
)
HOME_POSTER_DATA = []

try:
    df_poster = pd.read_csv(poster_csv_url, dtype=str)
    df_poster.columns = [str(c).strip().lower() for c in df_poster.columns]

    for _, row in df_poster.iterrows():
        raw_url = ""
        if "id" in df_poster.columns and pd.notna(row["id"]):
            raw_url = str(row["id"]).strip()
        elif "link" in df_poster.columns and pd.notna(row["link"]):
            raw_url = str(row["link"]).strip()

        raw_mode = ""
        if "mode" in df_poster.columns and pd.notna(row["mode"]):
            raw_mode = str(row["mode"]).strip()

        if raw_url and raw_url.lower() != "nan":
            url_formatted = format_drive_url(raw_url)
            if url_formatted:
                HOME_POSTER_DATA.append({
                    "url": url_formatted,
                    "transition": parse_transition_mode(raw_mode),
                })
except Exception:
    HOME_POSTER_DATA = []

# =====================================================================
# Registration Poster & Course List Loader
# =====================================================================
registration_sheet_id = "15Zt5BvHRvAusB7NJh8yf2WecvoUcR8kPR88Qoo_sN-4"
registration_csv_url = f"https://docs.google.com/spreadsheets/d/{registration_sheet_id}/export?format=csv"
REGISTRATION_DATA = []
REGISTRATION_COURSE_OPTIONS = []

try:
    df_reg = pd.read_csv(registration_csv_url, dtype=str)
    df_reg.columns = [str(c).strip().lower() for c in df_reg.columns]

    for _, row in df_reg.iterrows():
        raw_url = ""
        if "id" in df_reg.columns and pd.notna(row["id"]):
            raw_url = str(row["id"]).strip()
        elif "link" in df_reg.columns and pd.notna(row["link"]):
            raw_url = str(row["link"]).strip()

        raw_mode = ""
        if "mode" in df_reg.columns and pd.notna(row["mode"]):
            raw_mode = str(row["mode"]).strip()

        if raw_url and raw_url.lower() != "nan":
            url_formatted = format_drive_url(raw_url)
            if url_formatted:
                REGISTRATION_DATA.append({
                    "url": url_formatted,
                    "transition": parse_transition_mode(raw_mode),
                })

        if "course" in df_reg.columns and pd.notna(row["course"]):
            course_val = str(row["course"]).strip()
            if (
                course_val
                and course_val.lower() != "nan"
                and course_val not in REGISTRATION_COURSE_OPTIONS
            ):
                REGISTRATION_COURSE_OPTIONS.append(course_val)
except Exception:
    REGISTRATION_DATA = []
    REGISTRATION_COURSE_OPTIONS = []

about_sheet_id = "15bH_yee0Df3k6S8kCWgISfA0WcRUTV5vTjquG7e6L-I"
ABOUT_FILE_ID = "1Kt5Wks4HiUFmffHrfQSVMSDKy-YDpe1s"
FOUNDER_IMAGE_URL = "https://drive.google.com/thumbnail?id=1q4OJIWDS4f9hpYDPaiOjvZIfYA173b3z&sz=w1600"

about_statements = [
    (
        "Welcome to SIGNTECH SOLUTION, where our mission is empowering skills"
        " and advancing technology to accelerate your digital transformation."
    ),
    (
        "Our signature approach connects learning directly with real-world"
        " application through structured training courses, immersive hands-on"
        " exercises, and active project development."
    ),
    (
        "We focus on today’s most sought-after competencies, offering expert"
        " guidance in Python, Data Analytics, Artificial Intelligence, and"
        " Machine Learning."
    ),
    (
        "Partner with SIGNTECH SOLUTION today to elevate your workforce’s"
        " capabilities and drive sustained innovation. Together, we build"
        " lasting solutions."
    ),
]

try:
    about_csv_url = (
        f"https://docs.google.com/spreadsheets/d/{about_sheet_id}/export?format=csv"
    )
    df_about = pd.read_csv(about_csv_url, header=None)

    for _, row in df_about.iterrows():
        row_text = " ".join([str(x) for x in row.dropna().values]).lower()
        if "about us" in row_text or "about_us" in row_text:
            for item in row.dropna():
                val = str(item)
                m = re.search(r"(?:file/d/|id=)([\w-]+)", val)
                if m:
                    ABOUT_FILE_ID = m.group(1)
                    break

    for _, row in df_about.iterrows():
        row_text = " ".join([str(x) for x in row.dropna().values]).lower()
        if "founder" in row_text:
            for item in row.dropna():
                val = str(item)
                m = re.search(r"(?:file/d/|id=)([\w-]+)", val)
                if m:
                    FOUNDER_IMAGE_URL = f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w1600"
                    break

    extracted_statements = []
    for _, row in df_about.iterrows():
        row_vals = [
            str(v).strip()
            for v in row.dropna().values
            if str(v).strip() != "" and str(v).lower() != "nan"
        ]
        row_text = " ".join(row_vals)

        if re.search(r"statement\s*[1-4]", row_text, re.IGNORECASE):
            content_candidates = [
                v
                for v in row_vals
                if not re.match(
                    r"^(statement\s*[1-4]|\d+)$", v.strip(), re.IGNORECASE
                )
                and not ("http" in v.lower() or "drive.google" in v.lower())
            ]
            if content_candidates:
                extracted_statements.append(max(content_candidates, key=len))

    for idx in range(min(4, len(extracted_statements))):
        about_statements[idx] = extracted_statements[idx]
except Exception:
    pass

# =====================================================================
# Course Poster Data Loader
# =====================================================================
courses_sheet_id = "1ZrPa42sz-TO2_TubWqSqtSG3oJDoh9IFbvPFPTzbKDA"
courses_data = []

try:
    courses_csv_url = f"https://docs.google.com/spreadsheets/d/{courses_sheet_id}/export?format=csv"
    df_courses = pd.read_csv(courses_csv_url, header=None)

    for idx, row in df_courses.iterrows():
        first_col_val = str(row.iloc[0]).strip().lower()
        if first_col_val in ["no", "bil", "no.", "id"]:
            continue

        course_name = (
            str(row.iloc[1]).strip()
            if len(row) > 1 and pd.notna(row.iloc[1])
            else f"Course {idx + 1}"
        )

        drive_url = ""
        for val in row.dropna().values:
            val_str = str(val).strip()
            if (
                "drive.google.com" in val_str
                or "lh3.googleusercontent.com" in val_str
                or re.search(r"(?:file/d/|id=)([\w-]+)", val_str)
            ):
                drive_url = format_drive_url(val_str)
                if drive_url:
                    break

        if drive_url:
            courses_data.append({"title": course_name, "image_url": drive_url})
except Exception:
    courses_data = []

hrd_poster_sheet_id = "162VnRkYdmN5bL60zow0tYp7pYKGO9pkRvcBOewHAC5E"
hrd_poster_images = []

try:
    hrd_poster_csv_url = f"https://docs.google.com/spreadsheets/d/{hrd_poster_sheet_id}/export?format=csv"
    df_hrd_poster = pd.read_csv(hrd_poster_csv_url, header=None)
    for _, row in df_hrd_poster.iterrows():
        drive_url = ""
        for val in row.dropna().values:
            val_str = str(val).strip()
            if (
                "drive.google.com" in val_str
                or "googleusercontent.com" in val_str
                or re.search(r"(?:file/d/|id=)([\w-]+)", val_str)
            ):
                drive_url = format_drive_url(val_str)
                break
        if drive_url:
            hrd_poster_images.append(drive_url)
except Exception:
    hrd_poster_images = []

# =====================================================================
# Trainer Posters Loader
# =====================================================================
trainer_sheet_id = "1oblZ5x8vD8ovnjuZrgY_g6HaIEyjSSCrS4kRKg_W2wc"
TRAINER_1_IMAGE_URL = "https://drive.google.com/thumbnail?id=1Tn8OoQWlh9FgbEdU9sT6v54rxpFvAyAg&sz=w1600"
TRAINER_2_IMAGE_URL = "https://drive.google.com/thumbnail?id=1ZA-IbHB1PjEx1pEOsWn6FG-b8a77OBP_&sz=w1600"

try:
    trainer_csv_url = f"https://docs.google.com/spreadsheets/d/{trainer_sheet_id}/export?format=csv"
    df_trainer = pd.read_csv(trainer_csv_url, header=None)

    for _, row in df_trainer.iterrows():
        row_str = " ".join([str(x) for x in row.dropna().values]).lower()

        if "trainer1" in row_str or "trainer 1" in row_str:
            for val in row.dropna().values:
                val_str = str(val).strip()
                if "drive.google.com/file/d/" in val_str:
                    TRAINER_1_IMAGE_URL = format_drive_url(val_str)
                    break
        elif "trainer2" in row_str or "trainer 2" in row_str:
            for val in row.dropna().values:
                val_str = str(val).strip()
                if "drive.google.com/file/d/" in val_str:
                    TRAINER_2_IMAGE_URL = format_drive_url(val_str)
                    break
except Exception:
    pass

certificate_sheet_id = "1d7TnAs5_2IHyZV1Szhpa0O3Y9ZXnHtWb7en3e6xje5c"
certificate_images_data = []

try:
    cert_csv_url = f"https://docs.google.com/spreadsheets/d/{certificate_sheet_id}/export?format=csv"
    df_cert = pd.read_csv(cert_csv_url, header=None)
    for idx, row in df_cert.iterrows():
        vals = [str(v).strip() for v in row.dropna().values]
        row_str = " ".join(vals)
        if "drive.google.com" in row_str or "googleusercontent.com" in row_str:
            title_text = (
                vals[1]
                if len(vals) > 1 and not vals[1].startswith("http")
                else f"Image {len(certificate_images_data) + 1}"
            )
            img_url = ""
            for v in reversed(vals):
                if (
                    "http" in v
                    or "drive.google.com" in v
                    or "googleusercontent.com" in v
                ):
                    img_url = format_drive_url(v)
                    break
            if img_url:
                certificate_images_data.append(
                    {"title": title_text, "url": img_url}
                )
except Exception:
    certificate_images_data = []

wasap_fb_sheet_id = "15Tixtfx2zkR73eWle4bG3fYtr749EOoN2_G1-MpI-cQ"
try:
    wasap_fb_csv_url = f"https://docs.google.com/spreadsheets/d/{wasap_fb_sheet_id}/export?format=csv"
    df_social = pd.read_csv(wasap_fb_csv_url)

    WASAP_ICON_URL = (
        format_drive_url(df_social.iloc[0, 8])
        if df_social.shape[1] > 8
        else format_drive_url(df_social.iloc[0, 6])
    )
    FB_ICON_URL = (
        format_drive_url(df_social.iloc[1, 8])
        if df_social.shape[1] > 8
        else format_drive_url(df_social.iloc[1, 6])
    )
except Exception:
    WASAP_ICON_URL = "https://drive.google.com/thumbnail?id=1pM0gYwgzQLdrdagmBT1Y39yEkeb5jnHb&sz=w1600"
    FB_ICON_URL = "https://drive.google.com/thumbnail?id=1HTrn5yyYQWx96iKmUWb5n--I5-xo_0GE&sz=w1600"

from urllib.parse import quote

WASAP_MESSAGE = (
    "Salam sejahtera SIGNTECH SOLUTION.\n\n"
    "Saya berminat untuk mengetahui lebih lanjut mengenai "
    "program latihan profesional yang ditawarkan.\n\n"
    "Boleh kongsikan maklumat kursus, jadual latihan "
    "dan yuran penyertaan?\n\n"
    "Terima kasih."
)

WASAP_LINK = "https://wa.me/60178578028?text=" + quote(WASAP_MESSAGE)

FB_LINK = "https://www.facebook.com/profile.php?id=61587187642133"

# ==============================================================================
# COURSE SYLLABUS & CONTENT
# ==============================================================================
course_content_dict = {
    "python_system_dev": {
        "overview": (
            "This 3-day hands-on training programme equips participants with"
            " practical Python programming skills for system development."
            " Participants will learn Python fundamentals, programming logic,"
            " functions, object-oriented programming, file handling, database"
            " integration, CRUD operations, graphical user interface (GUI)"
            " development, validation, testing, and debugging, concluding with"
            " developing a functional Python-based mini system."
        ),
        "duration": "3 Days (21 Hours excluding lunch)",
        "mode": (
            "Full Time / Non E-Learning (Instructor-led, hands-on guided coding)"
        ),
        "hrd_status": "HRD Corp Claimable Course (Non Micro Credential)",
        "target_audience": (
            "Executives, Engineers, Technical Officers, IT Personnel, Junior"
            " Developers, Technical Staff, Supervisors & beginners with no"
            " prior coding experience."
        ),
        "syllabus_intro": (
            "Comprehensive 3-day curriculum focusing on practical system"
            " development from zero:"
        ),
        "modules": [
            (
                "Day 1 - Module 1: Getting Started with Python (Introduction,"
                " environment setup, writing and running the first program)"
            ),
            (
                "Day 1 - Module 2: Python Programming Fundamentals (Variables,"
                " data types, operators, user input/output, conditions, loops)"
            ),
            (
                "Day 1 - Module 3: Functions and Structured Coding (Creating"
                " functions, parameters, return values, basic error handling)"
            ),
            (
                "Day 2 - Module 4: Organising Applications (Modules, intro to"
                " OOP, classes & objects for beginners)"
            ),
            (
                "Day 2 - Module 5: File and Data Handling (Reading & writing"
                " files, storing and retrieving data)"
            ),
            (
                "Day 2 - Module 6: Database and CRUD Operations (SQLite"
                " connection, table creation & CRUD operations)"
            ),
            (
                "Day 3 - Module 7: Graphical User Interface (GUI) (GUI-based"
                " applications, windows, buttons, form fields, event linkage)"
            ),
            (
                "Day 3 - Module 8: Validation, Testing and Debugging (Input"
                " validation, bug tracking & code reliability)"
            ),
            (
                "Day 3 - Module 9: Mini System Development Project (Logic, GUI"
                " & DB integration, system demonstration & review)"
            ),
        ],
    },
    "data_science_ai": {
        "overview": (
            "This 3-day hands-on training programme introduces participants to"
            " Data Science using Python and Artificial Intelligence (AI)."
            " Designed for beginners from zero, starting from data handling"
            " before progressing to data preparation, analysis, visualisation,"
            " SQL basics, and introductory AI-based prediction with a mini"
            " project."
        ),
        "duration": "3 Days (21 Hours excluding lunch)",
        "mode": (
            "Full Time / Non E-Learning (Instructor-Led, Hands-on"
            " demonstration)"
        ),
        "hrd_status": "HRD Corp Claimable Course (Non Micro Credential)",
        "target_audience": (
            "Executives, Engineers, Technical Officers, IT Personnel, Analysts,"
            " Supervisors, Technical Staff & beginners with zero prior data"
            " science/AI experience."
        ),
        "syllabus_intro": (
            "Step-by-step curriculum connecting basic Python data handling to"
            " applied AI workflows:"
        ),
        "modules": [
            (
                "Day 1 - Module 1: Introduction to Data Science (Workflows,"
                " business applications, data types, quality & ethics)"
            ),
            (
                "Day 1 - Module 2: Python for Data Science (Environment setup,"
                " data structures, logic, NumPy & Pandas intro)"
            ),
            (
                "Day 1 - Module 3: Data Acquisition & Preparation (Importing"
                " CSV/Excel, missing values, duplicates, validation)"
            ),
            (
                "Day 2 - Module 4: Exploratory Data Analysis (EDA) (Descriptive"
                " statistics, filtering, grouping, aggregation & trends)"
            ),
            (
                "Day 2 - Module 5: Data Visualisation (Matplotlib charts, bar,"
                " line, scatter, histograms & clear storytelling)"
            ),
            (
                "Day 3 - Module 6: Data Integration & SQL Basics (Relational"
                " databases, SELECT, WHERE, GROUP BY)"
            ),
            (
                "Day 3 - Module 7: Introduction to AI & Machine Learning"
                " (Supervised/unsupervised, regression, classification,"
                " train-test split)"
            ),
            (
                "Day 3 - Module 8 & 9: Integrated Data Science Mini Project &"
                " Presentation (Practical modeling, demonstration & assessment)"
            ),
        ],
    },
    "certified_data_scientist": {
        "overview": (
            "This five-day professional programme develops practical skills in"
            " Python, automated file processing, REST API, cloud storage"
            " integration, data storytelling, exploratory data analysis,"
            " machine learning, and predictive modelling. Participants progress"
            " to an end-to-end capstone project and formal competency"
            " assessment."
        ),
        "duration": "5 Days (Full-Time Executive / Hands-on Lab)",
        "mode": "Instructor-Led, Hands-On & Project-Based",
        "hrd_status": "HRD Corp Claimable Course",
        "target_audience": (
            "Beginner to Working Professional (No prior programming experience"
            " required); Analysts, Officers & Developers."
        ),
        "syllabus_intro": (
            "Intensive 5-day professional curriculum featuring 70% practical"
            " hands-on training:"
        ),
        "modules": [
            (
                "Day 1: Environment Setup & Python Fundamentals (PyCharm, Pip,"
                " Data Types, Collections, Logic, Functions & Automation"
                " Script)"
            ),
            (
                "Day 2: Automated File I/O, API, Cloud & Data Storytelling"
                " (CSV/Excel/JSON, REST API, Google Drive/S3, Matplotlib,"
                " Seaborn & Plotly)"
            ),
            (
                "Day 3: Advanced Analytics & Exploratory Data Analysis (NumPy"
                " computing, Pandas DataFrames, Univariate/Bivariate EDA &"
                " Hypothesis)"
            ),
            (
                "Day 4: Applied Machine Learning & Predictive Modeling"
                " (Train-test split, Decision Tree, Random Forest, Metrics &"
                " K-Means Clustering)"
            ),
            (
                "Day 5: Professional Competency Assessment & Capstone Project"
                " (Theory MCQ, Real-time Practical Coding & Capstone Defense)"
            ),
        ],
    },
    "machine_learning": {
        "overview": (
            "A comprehensive practical masterclass on machine learning using"
            " Python and Scikit-learn. Equips participants with end-to-end"
            " skills in data preprocessing, supervised learning, unsupervised"
            " learning, model evaluation, and hands-on project delivery."
        ),
        "duration": "Executive Hands-on Lab Workshop",
        "mode": "Instructor-Led Hands-on Training",
        "hrd_status": "100% HRD Corp Claimable under SBL-Khas Scheme",
        "target_audience": (
            "Data Analysts, Software Engineers, Technical Specialists & IT"
            " Professionals looking to master ML models."
        ),
        "syllabus_intro": (
            "Structured hands-on modules focusing on Scikit-learn workflows and"
            " algorithm implementations:"
        ),
        "modules": [
            (
                "Module 1: Python & Machine Learning Environment Setup"
                " (PyCharm, Scikit-learn & ML workflows)"
            ),
            (
                "Module 2: Data Preparation for Machine Learning (Pandas data"
                " cleaning, feature selection, train-test split)"
            ),
            (
                "Module 3: Regression with Python (Linear Regression,"
                " predictions & evaluation metrics)"
            ),
            (
                "Module 4: Classification with Python (Decision models,"
                " Confusion Matrix, Precision, Recall, F1 Score)"
            ),
            (
                "Module 5: Unsupervised Learning & Clustering (K-Means"
                " clustering, Elbow Method & cluster visualisation)"
            ),
            (
                "Module 6: Hands-On Machine Learning Mini Project (Full"
                " pipeline implementation, evaluation & presentation)"
            ),
        ],
    },
    "power_bi": {
        "overview": (
            "A 1-day practical masterclass introducing business intelligence"
            " through Microsoft Power BI. Participants learn to connect data"
            " sources, clean and transform data with Power Query, model data"
            " with DAX calculations, dan bina papan pemuka eksekutif interaktif."
        ),
        "duration": "1 Day (Online / Virtual Masterclass)",
        "mode": "Instructor-Led Virtual Lab & Hands-on Exercises",
        "hrd_status": "HRD Corp Claimable Course",
        "target_audience": (
            "Business Analysts, Executives, Managers, Accountants & Data"
            " Enthusiasts wanting to build interactive reporting dashboards."
        ),
        "syllabus_intro": (
            "1-day intensive dashboard design and data modeling outline:"
        ),
        "modules": [
            (
                "Module 1: Getting Started with Power BI (Ecosystem overview,"
                " setup, connecting to Excel/data sources)"
            ),
            (
                "Module 2: Data Transformation dan Modelling (Power Query ETL,"
                " data relationships, DAX formulas & measures)"
            ),
            (
                "Module 3: Building Interactive Dashboards (Bar, pie, map,"
                " KPIs, slicers, drill-through & Power BI Service sharing)"
            ),
            (
                "Module 4: Assessment and Feedback (Practical dashboard project"
                " evaluation & Q&A session)"
            ),
        ],
    },
    "intro_python": {
        "overview": (
            "An executive introductory course on Python programming for"
            " workplace task automation and data processing. Covers fundamental"
            " syntax, data structures, user functions, TXT/CSV file handling,"
            " as well as exploratory data manipulation using Pandas and"
            " Matplotlib."
        ),
        "duration": "Executive Hands-On Guided Lab",
        "mode": "Hands-on Guided Lab Workshop",
        "hrd_status": "HRD Corp Claimable Course",
        "target_audience": (
            "Executives, Technical Officers, Support Staff, and beginners"
            " seeking to build workplace data automation skills."
        ),
        "syllabus_intro": "Practical, application-driven course modules:",
        "modules": [
            (
                "Module 1: Python Fundamentals & IDE Setup (PyCharm IDE,"
                " syntax, variables, data types, and arithmetic logic)"
            ),
            (
                "Module 2: Data Structures & Flow Control (Lists, Dictionaries,"
                " Tuples, if/else conditions, loops, and data filtering)"
            ),
            (
                "Module 3: Custom Functions & File Handling (def/return,"
                " standard modules, automated TXT/CSV processing)"
            ),
            (
                "Module 4: Applied Data Analysis & Charting (Pandas DataFrames,"
                " data cleaning, and Matplotlib visualisations)"
            ),
            (
                "Module 5: Mini Project & Workplace Automation (Real-world"
                " automation scripts, code reviews, and best practices)"
            ),
        ],
    },
    "default": {
        "overview": (
            "An intensive, industry-aligned professional training programme"
            " designed to deliver enterprise-grade competencies, practical"
            " skills, and real-world implementation capabilities."
        ),
        "duration": "3 – 5 Days (Full-Time Executive / Hands-on Lab)",
        "mode": (
            "In-Person (Hands-on Lab) / Instructor-Led Virtual Interactive"
        ),
        "hrd_status": "100% HRD Corp Claimable under SBL-Khas Scheme",
        "target_audience": (
            "Software Engineers, Technical Specialists & Working Professionals"
        ),
        "syllabus_intro": (
            "A comprehensive curriculum featuring intensive hands-on lab"
            " sessions, enterprise case studies, dan a Capstone Project:"
        ),
        "modules": [
            "Module 1: Foundations & Professional Environment Setup",
            "Module 2: Data Wrangling, Cleaning & Automated Processing",
            "Module 3: Applied System Logic, Analytics & Machine Learning",
            "Module 4: Practical Mini Project & Final Competency Showcase",
        ],
    },
}


def get_course_content_by_title(title, idx):
    t = title.lower()
    if "system development" in t:
        return course_content_dict["python_system_dev"]
    elif (
        "data science with python & ai" in t
        or "data science with python and ai" in t
        or "data science with python ai" in t
    ):
        return course_content_dict["data_science_ai"]
    elif "certified data scientist" in t:
        return course_content_dict["certified_data_scientist"]
    elif "machine learning" in t:
        return course_content_dict["machine_learning"]
    elif "power bi" in t:
        return course_content_dict["power_bi"]
    elif (
        "intro_python" in t
        or "introduction to python" in t
        or "pengenalan" in t
    ):
        return course_content_dict["intro_python"]

    index_mapping = {
        0: "data_science_ai",
        1: "intro_python",
        2: "certified_data_scientist",
        3: "intro_python",
        4: "machine_learning",
        5: "power_bi",
        6: "python_system_dev",
    }
    return course_content_dict.get(
        index_mapping.get(idx, "default"), course_content_dict["default"]
    )


def render_animated_poster_carousel(
    poster_items,
    container_id="poster-carousel",
    max_width="100%",
    initial_height=500,
):
    items_json = json.dumps(poster_items)
    carousel_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            *, *::before, *::after {{ box-sizing: border-box; }}
            html, body {{
                margin: 0;
                padding: 0;
                background-color: transparent;
                width: 100%;
                height: auto;
                overflow: visible;
            }}
            .stage-wrapper {{
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                padding: 0;
                margin: 0;
            }}
            .canvas-box {{
                width: 100%;
                max-width: {max_width};
                background: #080808;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 18px;
                padding: 12px;
                box-shadow: 0 16px 45px rgba(0, 0, 0, 0.95);
                perspective: 1200px;
                overflow: hidden;
                box-sizing: border-box;
                margin: 0;
            }}
            .inner-viewport {{
                position: relative;
                width: 100%;
                display: grid;
                grid-template-columns: 1fr;
                grid-template-rows: auto;
                overflow: hidden;
                border-radius: 12px;
                line-height: 0;
            }}
            .carousel-slide {{
                grid-area: 1 / 1 / 2 / 2;
                width: 100%;
                height: auto;
                display: block;
                border-radius: 12px;
                object-fit: contain;
                opacity: 0;
                pointer-events: none;
                backface-visibility: hidden;
                transition: transform 0.8s ease-in-out, opacity 0.8s ease-in-out, clip-path 0.8s ease-in-out;
            }}
            .carousel-slide.active {{
                opacity: 1 !important;
                z-index: 5;
                transform: none !important;
                clip-path: none !important;
                position: relative;
            }}

            /* TRANSITION OUT */
            .slide-out-fade {{ opacity: 0 !important; }}
            .slide-out-h {{ transform: translateX(-100%) !important; opacity: 0 !important; }}
            .slide-out-v {{ transform: translateY(-100%) !important; opacity: 0 !important; }}
            .slide-out-zoom {{ transform: scale(0.9) !important; opacity: 0 !important; }}
            .slide-out-flip {{ transform: rotateY(90deg) !important; opacity: 0 !important; }}
            .slide-out-wipe {{ clip-path: inset(0 100% 0 0) !important; }}

            /* TRANSITION IN */
            .slide-in-fade {{ opacity: 1 !important; }}
            .slide-in-h {{ transform: translateX(0) !important; opacity: 1 !important; }}
            .slide-in-v {{ transform: translateY(0) !important; opacity: 1 !important; }}
            .slide-in-zoom {{ transform: scale(1) !important; opacity: 1 !important; }}
            .slide-in-flip {{ transform: rotateY(0deg) !important; opacity: 1 !important; }}
            .slide-in-wipe {{ clip-path: inset(0 0 0 0) !important; }}
        </style>
    </head>
    <body>
        <div class="stage-wrapper">
            <div class="canvas-box" id="{container_id}-box">
                <div class="inner-viewport" id="{container_id}-viewport"></div>
            </div>
        </div>

        <script>
            const data = {items_json};
            const viewport = document.getElementById('{container_id}-viewport');
            const box = document.getElementById('{container_id}-box');
            const elements = [];

            function syncHeight() {{
                const boxH = box ? Math.ceil(box.getBoundingClientRect().height) : 0;
                const targetH = boxH > 50 ? boxH + 4 : 0;

                if (targetH > 50) {{
                    try {{
                        if (window.frameElement) {{
                            window.frameElement.style.height = targetH + 'px';
                            window.frameElement.style.minHeight = targetH + 'px';
                            window.frameElement.setAttribute('height', targetH);
                            if (window.frameElement.parentElement) {{
                                window.frameElement.parentElement.style.height = targetH + 'px';
                                window.frameElement.parentElement.style.minHeight = targetH + 'px';
                            }}
                        }}
                    }} catch (e) {{}}

                    window.parent.postMessage({{
                        type: 'streamlit:setFrameHeight',
                        height: targetH
                    }}, '*');
                }}
            }}

            if (typeof ResizeObserver !== 'undefined' && box) {{
                const ro = new ResizeObserver(() => syncHeight());
                ro.observe(box);
            }}

            data.forEach((item, index) => {{
                const img = document.createElement('img');
                img.src = item.url;
                img.className = 'carousel-slide';
                img.referrerPolicy = 'no-referrer';
                img.dataset.trans = item.transition || 'fade';

                if (index === 0) {{
                    img.classList.add('active');
                    img.style.zIndex = '5';
                }}
                img.onload = syncHeight;
                viewport.appendChild(img);
                elements.push(img);
            }});

            window.addEventListener('load', syncHeight);
            window.addEventListener('resize', syncHeight);
            setTimeout(syncHeight, 100);
            setTimeout(syncHeight, 400);
            setTimeout(syncHeight, 900);
            setTimeout(syncHeight, 1800);

            let currentIndex = 0;

            setInterval(() => {{
                if (elements.length <= 1) return;

                const prevIdx = currentIndex;
                const nextIdx = (currentIndex + 1) % elements.length;
                currentIndex = nextIdx;

                const curEl = elements[prevIdx];
                const nextEl = elements[nextIdx];
                const mode = nextEl.dataset.trans || 'fade';

                nextEl.style.transition = 'none';
                nextEl.className = 'carousel-slide';
                nextEl.style.zIndex = '10';

                if (mode === 'horizontal-slide') {{
                    nextEl.style.transform = 'translateX(100%)';
                    nextEl.style.opacity = '1';
                }} else if (mode === 'vertical-slide') {{
                    nextEl.style.transform = 'translateY(100%)';
                    nextEl.style.opacity = '1';
                }} else if (mode === 'zoom-fade') {{
                    nextEl.style.transform = 'scale(1.1)';
                    nextEl.style.opacity = '0';
                }} else if (mode === 'flip') {{
                    nextEl.style.transform = 'rotateY(-90deg)';
                    nextEl.style.opacity = '0';
                }} else if (mode === 'wipe') {{
                    nextEl.style.clipPath = 'inset(0 100% 0 0)';
                    nextEl.style.opacity = '1';
                }} else {{
                    nextEl.style.opacity = '0';
                }}

                void nextEl.offsetWidth;

                nextEl.style.transition = '';
                curEl.style.zIndex = '5';

                if (mode === 'horizontal-slide') {{
                    curEl.classList.add('slide-out-h');
                    nextEl.classList.add('slide-in-h');
                }} else if (mode === 'vertical-slide') {{
                    curEl.classList.add('slide-out-v');
                    nextEl.classList.add('slide-in-v');
                }} else if (mode === 'zoom-fade') {{
                    curEl.classList.add('slide-out-zoom');
                    nextEl.classList.add('slide-in-zoom');
                }} else if (mode === 'flip') {{
                    curEl.classList.add('slide-out-flip');
                    nextEl.classList.add('slide-in-flip');
                }} else if (mode === 'wipe') {{
                    curEl.classList.add('slide-out-wipe');
                    nextEl.classList.add('slide-in-wipe');
                }} else {{
                    curEl.classList.add('slide-out-fade');
                    nextEl.classList.add('slide-in-fade');
                }}

                setTimeout(() => {{
                    curEl.className = 'carousel-slide';
                    curEl.style.zIndex = '1';
                    curEl.style.opacity = '0';
                    curEl.style.transform = '';
                    curEl.style.clipPath = '';

                    nextEl.className = 'carousel-slide active';
                    nextEl.style.zIndex = '5';
                    syncHeight();
                }}, 820);
            }}, 5000);
        </script>
    </body>
    </html>
    """
    components.html(carousel_html, height=initial_height, scrolling=False)


# =====================================================================
# 4. Standardized CSS Styling
# =====================================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,500;0,600;0,700;0,800;1,600&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

    .stApp {
        background-color: #000000 !important;
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stAppDeployButton"],
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }

    .block-container {
        padding-top: 0.4rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1200px !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        letter-spacing: -0.2px;
    }

    label[data-testid="stWidgetLabel"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.90rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
        margin-bottom: 4px !important;
    }

    input, textarea, select {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.92rem !important;
        color: #f8fafc !important;
    }

    .header-banner-container {
        width: 100% !important;
        margin-bottom: 20px !important;
        text-align: center;
        background: #000000 !important;
        border: none !important;
        border-radius: 16px;
        padding: 0px !important;
        box-sizing: border-box;
    }

    .header-banner-img {
        width: 100% !important;
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
        border-radius: 8px;
        display: block;
        margin: 0 auto;
    }

    .footer-wrapper-container {
        width: 100% !important;
        position: relative !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-top: 36px !important;
        margin-bottom: 24px !important;
        background: transparent !important;
        box-sizing: border-box !important;
    }

    .footer-banner-img {
        width: 100% !important;
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
        border-radius: 8px !important;
        display: block !important;
        margin: 0 auto !important;
    }

    .social-btn-left {
        position: absolute !important;
        left: 14px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 10 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 44px !important;
        height: 44px !important;
        border-radius: 50% !important;
        overflow: hidden !important;
        transition: transform 0.25s ease, opacity 0.25s ease;
    }

    .social-btn-right {
        position: absolute !important;
        right: 14px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 10 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 44px !important;
        height: 44px !important;
        border-radius: 50% !important;
        overflow: hidden !important;
        transition: transform 0.25s ease, opacity 0.25s ease;
    }

    .social-btn-left:hover, .social-btn-right:hover {
        transform: translateY(-50%) scale(1.1) !important;
        opacity: 0.92;
    }

    .social-icon-img {
        width: 44px !important;
        height: 44px !important;
        object-fit: cover !important;
        border-radius: 50% !important;
        display: block !important;
        box-shadow: none !important;
        transform: scale(1.28) !important;
        clip-path: circle(38% at 50% 50%) !important;
    }

    div[data-testid="stHorizontalBlock"]:first-of-type {
        position: relative !important;
        margin-left: 10px !important;
        margin-right: -10px !important;
        width: calc(100% - 10px) !important;
    }

    [data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        padding: 0 6px !important;
    }

    [data-testid="column"] > div {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        flex-grow: 1 !important;
    }

    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton {
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }

    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 10px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        font-size: clamp(11px, 0.78vw, 13px) !important;
        letter-spacing: 0.3px !important;
        width: 100% !important;
        min-width: 100px !important;
        max-width: 120px !important;
        height: 40px !important;
        min-height: 40px !important;
        text-align: center !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        padding: 0 6px !important;
        margin: 0 auto !important;
        box-shadow: 0 2px 8px rgba(255, 255, 255, 0.12) !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button p,
    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button span {
        color: #000000 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        transition: color 0.25s ease !important;
    }

    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button:hover {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
        box-shadow: 0 4px 14px rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-1.5px) !important;
    }

    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button:hover p,
    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button:hover span {
        color: #ffffff !important;
    }

    .content-canvas-frame {
        width: 100%;
        margin-top: 36px !important;
        margin-bottom: 36px !important;
        padding: 24px;
        background: #080808 !important;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.95), 0 0 1px 1px rgba(255, 255, 255, 0.05);
        display: block;
        box-sizing: border-box;
    }

    .hrd-single-canvas {
        width: 100%;
        margin-top: 6px !important;
        margin-bottom: 16px !important;
        padding: 22px 24px;
        background: #080808 !important;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.95), 0 0 1px 1px rgba(255, 255, 255, 0.05);
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        height: 100%;
        flex-grow: 1;
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }

    .hrd-single-canvas:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 255, 255, 0.35);
        box-shadow: 0 16px 45px rgba(0, 0, 0, 1), 0 0 14px rgba(255, 255, 255, 0.1);
    }

    .hrd-poster-hover {
        position: relative;
        z-index: 1;
        transition: transform 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease !important;
    }

    .hrd-poster-hover:hover {
        transform: scale(1.1) !important;
        z-index: 20 !important;
        border-color: rgba(255, 215, 0, 0.6) !important;
        box-shadow: 0 22px 55px rgba(0, 0, 0, 1), 0 0 20px rgba(255, 215, 0, 0.2) !important;
    }

    .hrd-title {
        color: #ffffff;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin: 0 0 10px 0;
        letter-spacing: -0.2px;
    }

    .hrd-desc {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.92rem !important;
        color: #cbd5e1;
        line-height: 1.65;
        margin: 0;
    }

    .course-poster-frame {
        width: 100%;
        padding: 0px !important;
        background: #0b0e14 !important;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.9);
        box-sizing: border-box;
        position: relative;
        z-index: 1;
        transition: transform 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
        display: flex;
        flex-direction: column;
    }

    .course-poster-frame:hover {
        transform: scale(1.1);
        z-index: 20;
        border-color: rgba(255, 215, 0, 0.6);
        box-shadow: 0 22px 55px rgba(0, 0, 0, 1), 0 0 20px rgba(255, 215, 0, 0.2);
    }

    .course-poster-img {
        width: 100%;
        height: auto;
        border-radius: 17px;
        display: block;
        object-fit: cover;
        margin: 0 auto;
    }

    .about-poster-img {
        width: 100%;
        height: auto;
        border-radius: 14px;
        display: block;
        object-fit: cover;
        margin: 0 auto;
        border-bottom-left-radius: 0px !important;
        border-bottom-right-radius: 0px !important;
    }

    .statement-unified-container {
        width: 100%;
        background: linear-gradient(180deg, #0e1014 0%, #07080a 100%) !important;
        border: none !important;
        border-radius: 0px !important;
        box-sizing: border-box;
        margin: 0 !important;
        padding: 16px 0 !important;
    }

    .statement-section {
        padding: 18px 34px;
        border: none !important;
        box-sizing: border-box;
    }

    .statement-text {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: clamp(14.5px, 1.15vw, 16.5px) !important;
        line-height: 1.8 !important;
        color: #f8fafc !important;
        font-weight: 400 !important;
        text-align: justify !important;
        text-justify: inter-word !important;
        margin: 0;
        letter-spacing: 0.15px;
    }

    .founder-poster-section {
        width: 100%;
        margin-top: 0px !important;
        padding-top: 0px !important;
        display: block;
        border: none !important;
    }

    .founder-poster-img {
        width: 100%;
        height: auto;
        border-top-left-radius: 0px !important;
        border-top-right-radius: 0px !important;
        border-bottom-left-radius: 14px !important;
        border-bottom-right-radius: 14px !important;
        display: block;
        object-fit: cover;
        margin: 0 auto;
    }

    .course-details-canvas {
        width: 100%;
        margin-top: 10px;
        margin-bottom: 10px;
        padding: 24px 28px;
        background: #0a0d13 !important;
        border: 1.5px solid #233145;
        border-radius: 16px;
        box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.8), 0 8px 25px rgba(0, 0, 0, 0.7);
        box-sizing: border-box;
        animation: fadeIn 0.3s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .canvas-title {
        color: #ffd700;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.10rem !important;
        font-weight: 700 !important;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255, 215, 0, 0.3);
        padding-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        letter-spacing: 0.2px;
    }

    .canvas-text {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.92rem !important;
        color: #e2e8f0;
        line-height: 1.65;
    }

    .canvas-list {
        margin: 8px 0 0 18px;
        padding: 0;
        color: #cbd5e1;
    }

    .canvas-list li {
        margin-bottom: 6px;
    }

    button[aria-label="Details"],
    button[aria-label="Syllabus"] {
        background-color: #ffd700 !important;
        background-image: none !important;
        color: #000000 !important;
        border: 1px solid #eab308 !important;
        border-radius: 6px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        letter-spacing: 0.3px !important;
        width: 84px !important;
        min-width: 84px !important;
        max-width: 84px !important;
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        padding: 0px 4px !important;
        margin: 3px auto !important;
        line-height: 28px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 6px rgba(234, 179, 8, 0.35) !important;
        transition: all 0.2s ease !important;
    }

    button[aria-label="Details"] *,
    button[aria-label="Syllabus"] * {
        font-family: 'Montserrat', sans-serif !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        line-height: 28px !important;
        margin: 0 !important;
        padding: 0 !important;
        white-space: nowrap !important;
        transition: color 0.2s ease !important;
    }

    button[aria-label="Details"]:hover,
    button[aria-label="Syllabus"]:hover {
        background-color: #000000 !important;
        background-image: none !important;
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
        transform: translateY(-0.5px) !important;
        box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3) !important;
    }

    button[aria-label="Details"]:hover *,
    button[aria-label="Syllabus"]:hover * {
        color: #ffffff !important;
    }

    div[data-testid="stFormSubmitButton"] > button {
        background-color: #ffd700 !important;
        background-image: none !important;
        color: #000000 !important;
        border: 1px solid #eab308 !important;
        border-radius: 8px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.3px !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stFormSubmitButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button span {
        font-family: 'Montserrat', sans-serif !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #f59e0b !important;
        color: #000000 !important;
        border-color: #d97706 !important;
        box-shadow: 0 6px 20px rgba(245, 158, 11, 0.45) !important;
        transform: translateY(-1.5px) !important;
    }

    div[data-testid="stFormSubmitButton"] > button:hover p,
    div[data-testid="stFormSubmitButton"] > button:hover span {
        color: #000000 !important;
    }

    .cert-poster-card {
        width: 100% !important;
        margin: 0 0 8px 0 !important;
        padding: 8px !important;
        background: #080808 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 14px !important;
        box-sizing: border-box !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.8) !important;
        position: relative !important;
        z-index: 1 !important;
        transition: transform 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease !important;
    }

    .cert-poster-card:hover {
        transform: scale(1.1) !important;
        z-index: 20 !important;
        border-color: rgba(255, 215, 0, 0.6) !important;
        box-shadow: 0 22px 55px rgba(0, 0, 0, 1), 0 0 20px rgba(255, 215, 0, 0.2) !important;
    }

    /* =====================================================================
       Interactive & Professional Registration Form Styling (Non-Overlapping)
       ===================================================================== */
    div[data-testid="stElementContainer"]:has(iframe[title="streamlit_components_v1.html_v1"]) {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
        position: relative !important;
        z-index: 1 !important;
    }

    div[data-testid="stForm"] {
        background: linear-gradient(145deg, #0b0e14 0%, #06080c 100%) !important;
        border: 1px solid rgba(255, 215, 0, 0.25) !important;
        border-radius: 20px !important;
        padding: 32px 34px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.95), 0 0 25px rgba(255, 215, 0, 0.05) !important;
        max-width: 950px !important;
        margin: 8px auto 0 auto !important;
        position: relative !important;
        z-index: 2 !important;
        clear: both !important;
    }

    .reg-form-header {
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 18px;
        margin-bottom: 24px;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }

    .reg-form-title {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin: 0 !important;
    }

    .reg-form-subtitle {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        color: #94a3b8 !important;
        margin: 4px 0 0 0 !important;
    }

    .form-section-divider {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 22px 0 14px 0;
        padding-bottom: 6px;
        border-bottom: 1px dashed rgba(255, 255, 255, 0.12);
    }

    .form-step-pill {
        background: #ffd700;
        color: #000000;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 6px;
    }

    .form-section-label {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.95rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: 0.2px;
    }

    div[data-testid="stForm"] div[data-baseweb="input"] > div,
    div[data-testid="stForm"] div[data-baseweb="select"] > div,
    div[data-testid="stForm"] div[data-baseweb="textarea"] > div {
        background-color: #111622 !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 10px !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stForm"] div[data-baseweb="input"] > div:hover,
    div[data-testid="stForm"] div[data-baseweb="select"] > div:hover,
    div[data-testid="stForm"] div[data-baseweb="textarea"] > div:hover {
        border-color: rgba(255, 215, 0, 0.5) !important;
        background-color: #151b29 !important;
    }

    div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
    div[data-testid="stForm"] div[data-baseweb="select"] > div:focus-within,
    div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within {
        border-color: #ffd700 !important;
        box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.2) !important;
        background-color: #161d2c !important;
    }

    div[data-testid="stForm"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #111622 !important;
        border: 1.5px dashed rgba(255, 215, 0, 0.35) !important;
        border-radius: 12px !important;
        padding: 18px !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stForm"] section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #ffd700 !important;
        background-color: #151b29 !important;
    }

    .payment-info-box {
        background: rgba(59, 130, 246, 0.08);
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 14px 0 20px 0;
        font-size: 0.85rem;
        color: #cbd5e1;
        line-height: 1.5;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# 5. Header Banner
# =====================================================================
st.markdown(
    f"""
    <div class="header-banner-container">
        <img src="{HEADER_BANNER_URL}" class="header-banner-img" referrerpolicy="no-referrer" alt="Header Banner" />
    </div>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# 6. Top Navigation Bar
# =====================================================================
nav_items = [
    "Home",
    "About",
    "Courses",
    "HRD Corp",
    "Trainer",
    "Testimonials",
    "Registration",
]
cols = st.columns(len(nav_items))

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Home"

for i, item in enumerate(nav_items):
    with cols[i]:
        if st.button(item, key=f"nav_btn_{i}"):
            st.session_state.selected_page = item

# =====================================================================
# 7. Content Rendering by Active Route
# =====================================================================
current_page = st.session_state.selected_page

if current_page == "Home":
    st.markdown(
        "<div style='margin-top: 24px;'></div>", unsafe_allow_html=True
    )
    if HOME_POSTER_DATA:
        render_animated_poster_carousel(
            HOME_POSTER_DATA, container_id="home-poster", max_width="100%"
        )
    else:
        st.markdown(
            """
            <div class="content-canvas-frame" style="padding: 24px; text-align: center;">
                <p style="color: #b0b3b8; font-size: 15px;">No posters found in Google Sheets.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif current_page == "About":
    st.markdown(
        f"""
<div class="content-canvas-frame">
    <img src="https://drive.google.com/thumbnail?id={ABOUT_FILE_ID}&sz=w1600" 
         referrerpolicy="no-referrer"
         class="about-poster-img" 
         alt="About Us Poster" />
    <div class="statement-unified-container">
        <div class="statement-section">
            <p class="statement-text">{about_statements[0]}</p>
        </div>
        <div class="statement-section">
            <p class="statement-text">{about_statements[1]}</p>
        </div>
        <div class="statement-section">
            <p class="statement-text">{about_statements[2]}</p>
        </div>
        <div class="statement-section">
            <p class="statement-text">{about_statements[3]}</p>
        </div>
    </div>
    <div class="founder-poster-section">
        <img src="{FOUNDER_IMAGE_URL}" 
             referrerpolicy="no-referrer"
             class="founder-poster-img" 
             alt="Founder Poster" />
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

elif current_page == "Courses":
    if "course_view" not in st.session_state:
        st.session_state.course_view = {}

    if courses_data:
        st.markdown(
            "<div style='margin-top: 36px;'></div>", unsafe_allow_html=True
        )

        for idx, c in enumerate(courses_data):
            col_poster, col_buttons = st.columns(
                [8.8, 1.2], gap="small", vertical_alignment="center"
            )

            with col_poster:
                st.markdown(
                    f"""
                    <div class="course-poster-frame">
                        <img src="{c['image_url']}" 
                             referrerpolicy="no-referrer"
                             class="course-poster-img" 
                             alt="{c['title']}" />
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_buttons:
                if st.button("Details", key=f"details_{idx}"):
                    if st.session_state.course_view.get(idx) == "details":
                        st.session_state.course_view[idx] = None
                    else:
                        st.session_state.course_view[idx] = "details"
                    st.rerun()

                if st.button("Syllabus", key=f"syllabus_{idx}"):
                    if st.session_state.course_view.get(idx) == "syllabus":
                        st.session_state.course_view[idx] = None
                    else:
                        st.session_state.course_view[idx] = "syllabus"
                    st.rerun()

            active_tab = st.session_state.course_view.get(idx)
            content = get_course_content_by_title(c["title"], idx)

            if active_tab == "details":
                st.markdown(
                    f"""
            <div class="course-details-canvas">
                <div class="canvas-title">
                    <span>Course Overview — {c['title']}</span>
                    <span style="font-size: 0.8rem; color: #9ca3af; font-weight: normal;">(Click Details again to close)</span>
                </div>
                <div class="canvas-text">
                    <p>{content['overview']}</p>
                    <ul class="canvas-list">
                        <li><strong>Duration:</strong> {content['duration']}</li>
                        <li><strong>Delivery Mode:</strong> {content['mode']}</li>
                        <li><strong>HRD Corp Status:</strong> {content['hrd_status']}</li>
                        <li><strong>Target Audience:</strong> {content['target_audience']}</li>
                    </ul>
                </div>
            </div>
            """,
                    unsafe_allow_html=True,
                )

            elif active_tab == "syllabus":
                modules_html = "".join(
                    [f"<li>{m}</li>" for m in content["modules"]]
                )
                st.markdown(
                    f"""
            <div class="course-details-canvas" style="border-color: #3b82f6;">
                <div class="canvas-title" style="color: #60a5fa; border-color: rgba(96, 165, 250, 0.3);">
                    <span>Course Syllabus — {c['title']}</span>
                    <span style="font-size: 0.8rem; color: #9ca3af; font-weight: normal;">(Click Syllabus again to close)</span>
                </div>
                <div class="canvas-text">
                    <p>{content['syllabus_intro']}</p>
                    <ul class="canvas-list">
                        {modules_html}
                    </ul>
                </div>
            </div>
            """,
                    unsafe_allow_html=True,
                )

            is_last = idx == len(courses_data) - 1
            bottom_margin = "36px" if is_last else "14px"
            st.markdown(
                f"<div style='margin-bottom: {bottom_margin};'></div>",
                unsafe_allow_html=True,
            )

    else:
        st.markdown(
            """
    <div class="content-canvas-frame" style="padding: 24px; text-align: center;">
        <p style="color: #b0b3b8; font-size: 15px;">No course posters found in the Google Sheets database.</p>
    </div>
    """,
            unsafe_allow_html=True,
        )

elif current_page == "HRD Corp":
    poster_map = {
        0: hrd_poster_images[0] if len(hrd_poster_images) > 0 else "",
        3: hrd_poster_images[1] if len(hrd_poster_images) > 1 else "",
        4: hrd_poster_images[2] if len(hrd_poster_images) > 2 else "",
        7: hrd_poster_images[3] if len(hrd_poster_images) > 3 else "",
    }

    hrd_partitions = [
        {
            "title": "SBL-Khas Scheme",
            "desc": "",
            "is_image": True,
            "image_url": poster_map.get(0, ""),
        },
        {
            "title": (
                "Advance Your Career with Zero Out-of-Pocket Cost – 100% HRD"
                " Corp Claimable!"
            ),
            "desc": (
                "<strong>1. What Is HRD Corp & How Does It Benefit"
                " You?</strong><br><br>The Human Resources Development"
                " Corporation (HRD Corp) is a premier agency under Malaysia’s"
                " Ministry of Human Resources (KESUMA), dedicated to"
                " future-proofing the national workforce through comprehensive"
                " upskilling and reskilling initiatives.<br><br>Through"
                " mandatory monthly levy contributions paid by your employer,"
                " your organization maintains an active, dedicated corporate"
                " talent development fund. Under the SBL-Khas Scheme, course"
                " fees are disbursed directly from this pool, empowering you to"
                " enroll in high-impact technical workshops, master in-demand"
                " digital competencies, dan earn industry-recognized"
                " certifications without spending a single cent from your own"
                " pocket. It is an immediate, fully funded pathway to expand"
                " your professional capabilities, increase your workplace value,"
                " and accelerate long-term career growth."
            ),
            "is_image": False,
        },
        {
            "title": 'Why Your Employer Will Gladly Say "Yes"',
            "desc": (
                '<strong>2. Why Your Employer Will Gladly Say "Yes"</strong><br><br>'
                "Proposing a training program to your manager or HR department is a win-win move that delivers direct value back to the organization:<br><br>"
                "• <strong>Zero Out-of-Pocket Training Expenses:</strong> Course fees are covered using your company's existing levy balance under the HRD Corp Claimable Courses (HRDCCC) scheme, protecting operational cash flow.<br><br>"
                "• <strong>Tax Deductions:</strong> Levy payments and approved training investments qualify as deductible business expenses under Malaysian tax law.<br><br>"
                "• <strong>Immediate ROI for the Team:</strong> The practical competencies, industry standard practices, and emerging tools you master will be applied directly to drive company projects and team productivity."
            ),
            "is_image": False,
        },
        {
            "title": "Registered Training Provider",
            "desc": "",
            "is_image": True,
            "image_url": poster_map.get(3, ""),
        },
        {
            "title": "Attendance & Certification",
            "desc": "",
            "is_image": True,
            "image_url": poster_map.get(4, ""),
        },
        {
            "title": (
                "Fully Claimable Training Programs Designed for Industry Impact"
            ),
            "desc": (
                "<strong>3. Fully Claimable Training Programs Designed for"
                " Industry Impact</strong><br><br>As an HRD Corp-registered"
                " Training Provider, our syllabi meet rigorous quality standards"
                " and address real-world market demands.<br><br>We"
                " offer:<br><br>• <strong>Public Training Sessions:</strong>"
                " Interactive, multi-industry cohorts where you learn alongside"
                " peers and build valuable professional networks.<br><br>•"
                " <strong>Customized In-House Programs:</strong> Tailored"
                " curriculums built around your team’s specific operational"
                " bottlenecks and strategic goals.<br><br>• <strong>Professional"
                " & Technical Certifications:</strong> Credentialed learning"
                " paths that keep your qualifications relevant in a"
                " fast-evolving economy."
            ),
            "is_image": False,
        },
        {
            "title": "Simple Steps: How to Pitch This to Your Employer Today",
            "desc": (
                "<strong>4. Simple Steps: How to Pitch This to Your Employer"
                " Today</strong><br><br>Getting approval for your next"
                " training milestone takes just four straightforward"
                " steps:<br><br>• <strong>Choose Your Course:</strong> Browse"
                " our catalog and select the program that aligns with your role"
                " and career aspirations.<br><br>• <strong>Request an Official"
                " Proposal & Quotation:</strong> Contact us to receive the"
                " comprehensive course outline and itemized fee"
                " breakdown.<br><br>• <strong>Submit to Your HR /"
                " Manager:</strong> Share the proposal with your HR department"
                " so they can register the grant via the eTRIS portal prior to"
                " the course date.<br><br>• <strong>Attend and"
                " Upskill:</strong> Complete your training, earn your"
                " certificate, and bring actionable new capabilities back to"
                " your desk!"
            ),
            "is_image": False,
        },
        {
            "title": "Technical Support & Advisory",
            "desc": "",
            "is_image": True,
            "image_url": poster_map.get(7, ""),
        },
    ]

    st.markdown(
        "<div style='margin-top: 36px;'></div>", unsafe_allow_html=True
    )

    for row_idx in range(4):
        col1, col2 = st.columns(2, gap="medium")

        idx1 = row_idx * 2
        item1 = hrd_partitions[idx1]
        with col1:
            if item1.get("is_image") and item1.get("image_url"):
                st.markdown(
                    f"""
                    <div class="hrd-single-canvas hrd-poster-hover" style="padding: 0; overflow: hidden; background: #080808;">
                        <img src="{item1['image_url']}" 
                             referrerpolicy="no-referrer"
                             style="width: 100%; height: 100%; object-fit: cover; border-radius: 18px; display: block;" 
                             alt="{item1['title']}" />
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="hrd-single-canvas">
                        <h3 class="hrd-title">{item1['title']}</h3>
                        <p class="hrd-desc">{item1['desc']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        idx2 = row_idx * 2 + 1
        item2 = hrd_partitions[idx2]
        with col2:
            if item2.get("is_image") and item2.get("image_url"):
                st.markdown(
                    f"""
                    <div class="hrd-single-canvas hrd-poster-hover" style="padding: 0; overflow: hidden; background: #080808;">
                        <img src="{item2['image_url']}" 
                             referrerpolicy="no-referrer"
                             style="width: 100%; height: 100%; object-fit: cover; border-radius: 18px; display: block;" 
                             alt="{item2['title']}" />
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="hrd-single-canvas">
                        <h3 class="hrd-title">{item2['title']}</h3>
                        <p class="hrd-desc">{item2['desc']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

elif current_page == "Trainer":
    st.markdown(
        f"""
        <div style="margin-top: 24px; display: flex; flex-direction: column; gap: 16px;">
            <div class="hrd-single-canvas hrd-poster-hover" style="height: auto; flex-grow: 0; margin: 0 !important; padding: 0; overflow: hidden; background: #080808;">
                <img src="{TRAINER_1_IMAGE_URL}" 
                     referrerpolicy="no-referrer"
                     style="width: 100%; height: auto; max-height: 600px; object-fit: cover; border-radius: 18px; display: block; margin: 0 auto;" 
                     alt="Trainer 1 Poster - SIGNTECH SOLUTION" />
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; align-items: stretch;">
                <div class="hrd-single-canvas" style="display: flex; flex-direction: column; justify-content: flex-start; height: 100%; box-sizing: border-box; margin: 0 !important;">
                    <h3 class="hrd-title">Requirements & Criteria</h3>
                    <p class="hrd-desc" style="flex-grow: 1;">
                        • <strong>Subject Mastery:</strong> Proven hands-on industry expertise in your domain (IT, Software Architecture, AI, Data Science, or Enterprise Systems).<br><br>
                        • <strong>Instructional Track Record:</strong> Prior experience conducting corporate workshops, bootcamps, or executive training labs.<br><br>
                        • <strong>Certifications:</strong> Professional credentials or recognized train-the-trainer qualifications (e.g., HRD Corp TTT) are an added advantage.<br><br>
                        • <strong>Delivery Commitment:</strong> Dedication to structured module preparation, syllabus compliance, and objective learner evaluation.
                    </p>
                </div>
                <div class="hrd-single-canvas" style="display: flex; flex-direction: column; justify-content: flex-start; height: 100%; box-sizing: border-box; margin: 0 !important;">
                    <h3 class="hrd-title">Trainer Attributes</h3>
                    <p class="hrd-desc" style="flex-grow: 1;">
                        • <strong>Engaging & Interactive:</strong> Ability to simplify complex technical topics into practical, workplace-applicable solutions.<br><br>
                        • <strong>Articulate Communication:</strong> Strong verbal presentation capabilities paired with structured, clear instructional pacing.<br><br>
                        • <strong>Learner-Centric Mindset:</strong> Patient, encouraging, and focused on tangible learner outcomes and milestone completion.<br><br>
                        • <strong>Professional Excellence:</strong> High ethical standards, punctuality, and seamless collaboration with event program managers.<br><br>
                        • <strong>Adaptive Classroom Management:</strong> Ability to dynamically tailor delivery pace, provide agile troubleshooting during live hands-on labs, and support participants across varying skill levels.
                    </p>
                </div>
            </div>
            <div class="hrd-single-canvas hrd-poster-hover" style="height: auto; flex-grow: 0; margin: 4px 0 16px 0 !important; padding: 0; overflow: hidden; background: #080808;">
                <img src="{TRAINER_2_IMAGE_URL}" 
                     referrerpolicy="no-referrer"
                     style="width: 100%; height: auto; max-height: 600px; object-fit: cover; border-radius: 18px; display: block; margin: 0 auto;" 
                     alt="Trainer 2 Poster - SIGNTECH SOLUTION" />
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("trainer_registration_form", clear_on_submit=False):
        st.markdown(
            """
            <div class="reg-form-header">
                <div>
                    <h3 class="reg-form-title">Trainer Registration Form</h3>
                    <p class="reg-form-subtitle">Submit your credentials and expertise below to join our accredited corporate trainer panel. Fields marked with <span style="color:#ffd700; font-weight:700;">*</span> are mandatory.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- SECTION 01: PERSONAL & CONTACT DETAILS ---
        st.markdown(
            """
            <div class="form-section-divider" style="margin-top: 4px;">
                <span class="form-step-pill">01</span>
                <span class="form-section-label">Personal & Contact Information</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        full_name = st.text_input(
            "Full Name *",
            placeholder="e.g. Ali bin Hassan",
        )

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            phone_number = st.text_input(
                "Phone Number / WhatsApp *",
                placeholder="e.g. +6012-3456789",
            )
        with col_c2:
            email_address = st.text_input(
                "Email Address *",
                placeholder="e.g. ali.hassan@example.com",
            )

        current_location = st.text_input(
            "Current Location / Address",
            placeholder="e.g. Kuala Lumpur, Malaysia",
        )

        # --- SECTION 02: PROFESSIONAL BACKGROUND & EXPERTISE ---
        st.markdown(
            """
            <div class="form-section-divider">
                <span class="form-step-pill">02</span>
                <span class="form-section-label">Professional Background & Domain Expertise</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_occ, col_exp = st.columns(2)
        with col_occ:
            current_occupation = st.text_input(
                "Current Occupation / Role",
                placeholder="e.g. Senior Data Scientist / Corporate Trainer",
            )
        with col_exp:
            area_of_expertise = st.text_input(
                "Areas of Expertise",
                placeholder=(
                    "e.g. Python, Machine Learning, Power BI, Cloud Architecture"
                ),
            )

        certifications = st.text_area(
            "Professional Certifications & Accreditations",
            placeholder=(
                "e.g. HRD Corp Certified Trainer (TTT), AWS Certified Solutions"
                " Architect, MBOT Ts., etc."
            ),
            height=105,
        )

        # --- SECTION 03: CURRICULUM VITAE / RESUME ---
        st.markdown(
            """
            <div class="form-section-divider">
                <span class="form-step-pill">03</span>
                <span class="form-section-label">Supporting Document (CV / Resume)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_cv = st.file_uploader(
            "Upload CV / Resume (PDF, DOC, DOCX) *",
            type=["pdf", "doc", "docx"],
            help="Please upload your latest resume or CV in PDF or Word format.",
        )

        st.markdown(
            """
            <div class="payment-info-box">
                <strong>Application Review:</strong> Our academic and technical panel reviews all trainer applications within 3–5 working days. Shortlisted candidates will be contacted for a syllabus alignment and micro-teaching session.
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            "Submit Trainer Application →",
            use_container_width=True,
        )

        if submitted:
            if (
                not full_name.strip()
                or not phone_number.strip()
                or not email_address.strip()
            ):
                st.error(
                    "Please complete all mandatory fields (*): Full Name,"
                    " Phone/WhatsApp, and Email Address."
                )
            elif uploaded_cv is None:
                st.warning(
                    "Please attach your CV or Resume document before"
                    " submitting."
                )
            else:
                payload = {
                    "full_name": full_name.strip(),
                    "phone_number": phone_number.strip(),
                    "email": email_address.strip(),
                    "location": current_location.strip(),
                    "occupation": current_occupation.strip(),
                    "expertise": area_of_expertise.strip(),
                    "certifications": certifications.strip(),
                }

                with st.spinner("Saving your application to server..."):
                    success, msg = append_trainer_to_ftp_csv(
                        payload, uploaded_cv
                    )

                if success:
                    st.balloons()
                    st.success(
                        f"Application successfully submitted for {full_name.strip()}! "
                        " Data and resume have been submitted."
                    )
                else:
                    st.error(
                        f"Failed to record application to FTP hosting: {msg}"
                    )

elif current_page == "Testimonials":
    st.markdown(
        "<div style='margin-top: 15px;'></div>", unsafe_allow_html=True
    )

    if certificate_images_data:
        cert_cards_html = "".join([
            f"""
            <div class="cert-poster-card">
                <img src="{cert_item['url']}" 
                     referrerpolicy="no-referrer"
                     class="course-poster-img" 
                     style="border-radius: 10px; width: 100%; height: auto; display: block; margin: 0 auto;" 
                     alt="Certificate Poster {idx + 1}" />
            </div>
            """
            for idx, cert_item in enumerate(certificate_images_data)
        ])

        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; width: 100%;">
                {cert_cards_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="content-canvas-frame" style="padding: 24px; text-align: center;">
                <p style="color: #b0b3b8; font-size: 15px;">No certificate posters found in the Google Sheets database.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif current_page == "Registration":
    st.markdown(
        "<div style='margin-top: 25px;'></div>", unsafe_allow_html=True
    )

    if REGISTRATION_DATA:
        render_animated_poster_carousel(
            REGISTRATION_DATA,
            container_id="reg-poster",
            max_width="665px",
            initial_height=840,
        )
    else:
        st.markdown(
            """
            <div class="content-canvas-frame" style="max-width: 665px; margin-left: auto; margin-right: auto; padding: 24px; text-align: center; margin-bottom: 18px !important;">
                <p style="color: #b0b3b8; font-size: 15px;">No registration posters found in Google Sheets.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------
    # Workshop Registration Form (Saves to httpdocs/Workshop/registration.csv)
    # -----------------------------------------------------------------
    course_title_options = list(REGISTRATION_COURSE_OPTIONS)
    if not course_title_options:
        course_title_options = [
            "Professional Python for System Development",
            "Data Science with Python & AI",
            "Certified Data Scientist",
            "Machine Learning with Python",
            "Microsoft Power BI Masterclass",
            "Introduction to Python Programming",
        ]

    with st.form("workshop_registration_form", clear_on_submit=False):
        st.markdown(
            """
            <div class="reg-form-header">
                <div>
                    <h3 class="reg-form-title">Workshop Registration Form</h3>
                    <p class="reg-form-subtitle">Complete your participant details below to reserve your seat. Fields marked with <span style="color:#ffd700; font-weight:700;">*</span> are mandatory.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- SECTION 01: PERSONAL DETAILS ---
        st.markdown(
            """
            <div class="form-section-divider" style="margin-top: 4px;">
                <span class="form-step-pill">01</span>
                <span class="form-section-label">Participant Personal Information</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        full_name = st.text_input(
            "Full Name (as per IC or Passport) *",
            placeholder="e.g. Ahmad bin Mohd Yusof",
        )

        col_ic, col_gender = st.columns(2)
        with col_ic:
            ic_passport = st.text_input(
                "Identity Card / Passport Number *",
                placeholder="e.g. 900101-14-5566 / A12345678",
            )
        with col_gender:
            gender = st.selectbox(
                "Gender *",
                options=["Male", "Female"],
            )

        col_phone, col_email = st.columns(2)
        with col_phone:
            phone_num = st.text_input(
                "Phone Number / WhatsApp *",
                placeholder="e.g. +6012-3456789",
            )
        with col_email:
            email_addr = st.text_input(
                "Official / Active Email Address *",
                placeholder="e.g. ahmad.yusof@example.com",
            )

        mailing_address = st.text_input(
            "Mailing / Office Address (Optional)",
            placeholder="e.g. No. 12, Jalan Teknologi 1, Cyberjaya, Selangor",
        )

        # --- SECTION 02: ORGANISATION & ACADEMIC ---
        st.markdown(
            """
            <div class="form-section-divider">
                <span class="form-step-pill">02</span>
                <span class="form-section-label">Organisation & Professional Profile</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_company, col_role = st.columns(2)
        with col_company:
            company_name = st.text_input(
                "Company / Organisation / Institution Name",
                placeholder="e.g. Telekom Malaysia / PETRONAS / Universiti Malaya",
            )
        with col_role:
            job_title = st.text_input(
                "Current Job Title / Role",
                placeholder="e.g. Data Analyst / IT Executive / Systems Engineer",
            )

        academic_qualification = st.selectbox(
            "Highest Academic Qualification",
            options=[
                "Doctor of Philosophy (PhD)",
                "Master's Degree",
                "Bachelor's Degree",
                "Diploma",
                "Certificate / STPM / SPM",
                "Others",
            ],
        )

        # --- SECTION 03: PROGRAMME & PAYMENT ---
        st.markdown(
            """
            <div class="form-section-divider">
                <span class="form-step-pill">03</span>
                <span class="form-section-label">Programme Selection & Payment Method</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_course, col_pay = st.columns([1.3, 1])
        with col_course:
            selected_course = st.selectbox(
                "Course / Workshop Selection *",
                options=course_title_options,
            )
        with col_pay:
            payment_method = st.selectbox(
                "Payment Method *",
                options=[
                    "HRD Corp Claimable (SBL-Khas)",
                    "Company Sponsored (Invoice / PO)",
                    "Individual Payment (Online Banking FPX)",
                    "Credit / Debit Card",
                    "Government Order (Local Order / LO)",
                ],
            )

        st.markdown(
            """
            <div class="payment-info-box">
                <strong>Note:</strong> Official quotation, course brochure, and HRD Corp grant application guidelines (eTRIS) will be emailed to you within 24 working hours upon registration.
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted_reg = st.form_submit_button(
            "Complete Registration →",
            use_container_width=True,
        )

        if submitted_reg:
            if (
                not full_name.strip()
                or not ic_passport.strip()
                or not phone_num.strip()
                or not email_addr.strip()
            ):
                st.error(
                    "Please fill in all mandatory fields (*): Full Name,"
                    " Identity Card / Passport Number, Phone Number / WhatsApp,"
                    " and Email Address."
                )
            else:
                reg_payload = {
                    "full_name": full_name.strip(),
                    "ic_passport": ic_passport.strip(),
                    "gender": gender,
                    "phone": phone_num.strip(),
                    "email": email_addr.strip(),
                    "address": mailing_address.strip(),
                    "company": company_name.strip(),
                    "job_title": job_title.strip(),
                    "course": selected_course,
                    "academic_status": academic_qualification,
                    "payment_method": payment_method,
                }

                with st.spinner("Submitting your registration to the server..."):
                    reg_success, reg_msg = append_registration_to_ftp_csv(
                        reg_payload
                    )

                if reg_success:
                    st.balloons()
                    st.success(
                        f"Registration successfully submitted for {full_name.strip()} for '{selected_course}'! "
                        f"Details have been recorded to '{REMOTE_WORKSHOP_DIR}/{REGISTRATION_FILENAME}' on the hosting server."
                    )
                else:
                    st.error(
                        f"Failed to record registration to FTP hosting: {reg_msg}"
                    )

else:
    st.markdown(
        f"""
        <div class="content-canvas-frame" style="min-height: 400px; padding: 28px;">
            <div style="width: 100%; align-self: flex-start;">
                <h2 style="color: #ffffff; font-weight: 700; margin-bottom: 15px; border-bottom: 2px solid rgba(255,255,255,0.2); padding-bottom: 10px; font-family: 'Montserrat', sans-serif;">{current_page}</h2>
                <p style="font-size: 0.95rem; color: #b0b3b8;">
                    Welcome to the <strong>{current_page}</strong> section.
                </p>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

# =====================================================================
# 8. Footer Banner & Social Media Links
# =====================================================================
st.markdown(
    f"""
    <div class="footer-wrapper-container">
        <a href="{WASAP_LINK}" target="_blank" class="social-btn-left" title="WhatsApp">
            <img src="{WASAP_ICON_URL}" class="social-icon-img" referrerpolicy="no-referrer" alt="WhatsApp" />
        </a>
        <img src="{FOOTER_BANNER_URL}" class="footer-banner-img" referrerpolicy="no-referrer" alt="Footer Banner" />
        <a href="{FB_LINK}" target="_blank" class="social-btn-right" title="Facebook">
            <img src="{FB_ICON_URL}" class="social-icon-img" referrerpolicy="no-referrer" alt="Facebook" />
        </a>
    </div>
""",
    unsafe_allow_html=True,
)