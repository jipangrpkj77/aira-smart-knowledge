"""AIRA Smart Knowledge V3.0: safe, local RAG over strictly allowlisted website data.

No execution of the Streamlit website. No FTP credentials, form submissions,
private user records, or arbitrary spreadsheet rows are ingested.
"""
import ast
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
from urllib.parse import quote
from urllib.request import Request, urlopen
import csv
import io

ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'main_12-11-2026.py'
DB_FILE = ROOT / 'knowledge' / 'aira_knowledge.sqlite3'
INTERVAL = max(300, int(os.environ.get('AIRA_SYNC_SECONDS', '1800')))

# These IDs are from the website source and identify *catalogue* content only.
# Important: NO forms response sheets, FTP data, participant records, or CVs.
ALLOWED_SHEETS = {
    'course_catalogue': ('1ZrPa42sz-TO2_TubWqSqtSG3oJDoh9IFbvPFPTzbKDA', 'courses'),
    'registration_catalogue': ('15Zt5BvHRvAusB7NJh8yf2WecvoUcR8kPR88Qoo_sN-4', 'registration'),
    'about_statements': ('15bH_yee0Df3k6S8kCWgISfA0WcRUTV5vTjquG7e6L-I', 'about'),
}

DENY = re.compile(r'(?i)(password|passwd|secret|api[_ -]?key|token|ftp_pass|ftp_user|private[_ -]?key|credential|BEGIN [A-Z ]*PRIVATE KEY|sk-proj-|sk-[A-Za-z0-9]{15,})')
EMAIL = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
PHONE = re.compile(r'(?<!\d)(?:\+?60|0)1\d[ -]?\d{3,4}[ -]?\d{4}(?!\d)')
ID_NUM = re.compile(r'(?<!\d)\d{6}-?\d{2}-?\d{4}(?!\d)')
WHITESPACE = re.compile(r'\s+')
LOCK = threading.Lock()
STATE = {'running': False,'last_completed':None,'last_error':None,'sources':{},'last_result':None}


def cleanse(text):
    text = html.unescape(re.sub(r'<[^>]*>', ' ', str(text)))
    text = WHITESPACE.sub(' ', text).strip()
    if DENY.search(text):return ''
    # Keep official catalogue items only: if source contains PII, redact, never store.
    text = EMAIL.sub('[email redacted]', text)
    text = ID_NUM.sub('[id redacted]', text)
    text = PHONE.sub('[phone redacted]', text)
    return text[:4000]


def connection():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(DB_FILE,timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, source TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, checksum TEXT NOT NULL)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_entries_source ON entries(source)')
    return conn


def find_named_assignment(tree, name):
    for node in ast.walk(tree):
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            if any(isinstance(t,ast.Name) and t.id==name for t in targets):
                return node.value
    return None


def literal(node,default=None):
    try:return ast.literal_eval(node)
    except (ValueError,TypeError,SyntaxError,MemoryError):return default


def local_documents():
    if not SITE.exists(): raise FileNotFoundError('Fail main_12-11-2026.py belum disalin ke folder ini')
    # Parse only: never import or execute site; never inspect FTP constants.
    tree=ast.parse(SITE.read_text(encoding='utf-8-sig'))
    docs=[]
    def add(title,text):
        text=cleanse(text)
        if len(text)>25: docs.append((title,text))
    courses=literal(find_named_assignment(tree,'course_content_dict'),{})
    if isinstance(courses,dict):
        for name, data in courses.items():
            if name=='default' or not isinstance(data,dict):continue
            details=[]
            for label,key in [('Overview','overview'),('Duration','duration'),('Mode','mode'),('HRD Corp status','hrd_status'),('Target audience','target_audience'),('Syllabus','syllabus_intro')]:
                value=data.get(key,'')
                if isinstance(value,str): details.append(f'{label}: {value}')
            for module in data.get('modules',[]):
                if isinstance(module,str): details.append('Module: '+module)
            # Split within document if long, do not destroy module boundaries.
            for i, chunk in enumerate(chunk_lines(details,1300)):
                add(f'Course {name} • {i+1}',f'Course name / code: {name}. '+chunk)
    about=literal(find_named_assignment(tree,'about_statements'),[])
    if isinstance(about,list):
        for i,statement in enumerate(about):
            if isinstance(statement,str):add(f'About SIGNTECH • {i+1}',statement)
    # Restrict this extraction to *hrd_partitions* and textual descriptions only.
    hrd=find_named_assignment(tree,'hrd_partitions')
    if isinstance(hrd,ast.List):
        for row in hrd.elts:
            if not isinstance(row,ast.Dict):continue
            d={literal(k):literal(v) for k,v in zip(row.keys,row.values)}
            title=d.get('title')
            desc=d.get('desc')
            if isinstance(title,str) and isinstance(desc,str) and desc:
                add('HRD Corp • '+title,desc)
    # Website registration and trainer sections are public program metadata,
    # not form submissions. Use only explicit constant labels known from site.
    add('Trainer • Application', 'SIGNTECH SOLUTION welcomes industry experts as trainers. Trainer registration requests contact information, areas of expertise, professional certifications, and an uploaded CV or resume. Do not ask visitors to send sensitive personal information in the chat; use the official website Trainer form.')
    add('Registration • Workshop', 'SIGNTECH SOLUTION website has a Registration page with a Workshop Registration Form. Visitors can select a course or workshop and a payment method. They should use the website registration form; AIRA does not collect IC or passport details.')
    add('Contact • Official links', 'WhatsApp official customer enquiry: https://wa.me/60178578028 . Facebook official page: https://www.facebook.com/profile.php?id=61587187642133 . These are public contact links.')
    return docs


def chunk_lines(lines,limit):
    output=[]; current=''
    for line in lines:
        line=str(line).strip()
        if not line:continue
        if current and len(current)+len(line)+2>limit:
            output.append(current);current=''
        if len(line)>limit:
            for j in range(0,len(line),limit):
                if current:output.append(current);current=''
                output.append(line[j:j+limit])
        else:current+=(('; ' if current else '')+line)
    if current:output.append(current)
    return output


def download_csv(sheet_id):
    url=f'https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/export?format=csv'
    req=Request(url,headers={'User-Agent':'AIRA-SIGNTECH/3.0 (public catalogue sync)'})
    with urlopen(req,timeout=12) as response:
        if 'text/html' in response.headers.get('Content-Type','').lower():
            raise ValueError('Google Sheet bukan CSV awam / akses disekat')
        content=response.read(750_001)
        if len(content)>750_000:raise ValueError('CSV terlalu besar')
    return list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))


def sheet_documents(key,kind,rows):
    docs=[]
    if kind=='courses':
        # Website itself uses column index 1 for course title; never ingest raw rows.
        for r in rows[:200]:
            if len(r)<2:continue
            title=cleanse(r[1]); first=(r[0].strip().lower() if r else '')
            if title and title.lower() not in ('course','course name','name','nan','title') and first not in ('bil','no','no.','id'):
                # Explicit title only. Image URLs do not contain reliable brochure text.
                docs.append(('Course catalogue • '+title,'SIGNTECH SOLUTION lists the programme: '+title))
    elif kind=='registration':
        if not rows:return []
        headers=[v.lower().strip() for v in rows[0]]
        if 'course' not in headers:return []
        i=headers.index('course')
        for r in rows[1:200]:
            title=cleanse(r[i]) if len(r)>i else ''
            if title and title.lower()!='nan': docs.append(('Registration course option • '+title,'Programme available in the website registration selection: '+title))
    elif kind=='about':
        for r in rows[:80]:
            if not any(re.search(r'(?i)statement\s*[1-4]',c) for c in r):continue
            values=[cleanse(c) for c in r]
            values=[v for v in values if len(v)>45 and not v.lower().startswith(('https://','http://'))]
            if values: docs.append(('About statement • SIGNTECH',max(values,key=len)))
    # Never store raw source rows, identifiers, images, or personal data.
    return list(dict.fromkeys(docs))[:120]


def replace_source(conn,source, docs):
    clean=[]
    for title,body in docs:
        title=cleanse(title)[:180];body=cleanse(body)
        if title and body: clean.append((source,title,body,hashlib.sha256(body.encode()).hexdigest()))
    with conn:
        conn.execute('DELETE FROM entries WHERE source=?',(source,))
        conn.executemany('INSERT INTO entries (source,title,content,checksum) VALUES (?,?,?,?)',clean)
    return len(clean)


def sync(include_remote=True):
    if not LOCK.acquire(blocking=False):return {'running':True,'message':'Penyegerakan lain sedang berjalan'}
    STATE['running']=True
    result={'sources':{},'warnings':[],'finished':None}
    try:
        with connection() as con:
            try:
                count=replace_source(con,'website:main_12-11-2026.py',local_documents())
                result['sources']['website']=count
            except Exception as e:result['warnings'].append('Website: '+str(e))
            if include_remote:
                for key,(sheet_id,kind) in ALLOWED_SHEETS.items():
                    try:
                        rows=download_csv(sheet_id)
                        records=sheet_documents(key,kind,rows)
                        if not records:raise ValueError('Tiada kandungan katalog yang disahkan (cache lama dikekalkan)')
                        count=replace_source(con,'google_sheets:'+key,records)
                        result['sources'][key]=count
                    except Exception as e:
                        result['warnings'].append(key+': '+str(e))
            result['total']=con.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
        result['finished']=int(time.time())
        STATE['last_completed']=result['finished']
        STATE['last_error']='; '.join(result['warnings']) if result['warnings'] else None
        STATE['last_result']=result
        return result
    finally:
        STATE['running']=False;LOCK.release()

TOKENIZE=re.compile(r'[\w]+',re.UNICODE)
STOP=set('dan yang untuk dengan dalam dari pada ini itu saya anda the and for with from are have what which kepada boleh bolehkan juga atau to a an is of di ke ialah apakah bagaimana when where why what your you'.split())
ALIASES={
 'python':['programming','pengaturcaraan'],
 'baru':['beginner','introduction','intro','asas'],
 'mula':['beginner','introduction','intro','asas'],
 'pemula':['beginner','introduction','intro','asas'],
 'beginner':['intro','introduction','asas','baru'],
 'asas':['intro','introduction','beginner'],
 'kursus':['course','training','program','latihan'],
 'training':['kursus','latihan','programme'],
 'hrd':['claimable','tuntutan','corp','sbl'],
 'register':['registration','daftar','pendaftaran'],
 'daftar':['register','registration','pendaftaran'],
 'bayaran':['payment','yuran','fees'],
 'yuran':['fees','price','harga'],
 'trainer':['jurulatih','pengajar'],
 'machine':['learning','pembelajaran','mesin'],
 'bi':['power','dashboard'],
}

def terms(text):
    output=[]
    for t in TOKENIZE.findall(text.lower()):
        if len(t)<2 or t in STOP:continue
        output.append(t)
        output.extend(ALIASES.get(t,[]))
    return output


def retrieve(query,limit=4):
    q=terms(query)
    if not q:return []
    # Beginner queries should prioritize the entry-level introductory offering.
    beginner=any(t in set(q) for t in ['beginner','introduction','intro','asas','baru'])
    with connection() as con: rows=con.execute('SELECT source,title,content FROM entries').fetchall()
    if not rows:return []
    scored=[]
    for source,title,content in rows:
        title_terms=terms(title);body_terms=terms(content)
        title_set=set(title_terms);body_set=set(body_terms)
        hits=sum((3 if term in title_set else 0)+(1 if term in body_set else 0) for term in set(q))
        if beginner and ('intro_python' in title or 'introduction to python' in title.lower()):hits+=16
        if hits:
            scored.append((hits,source,title,content))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{'source':s,'title':t,'text':c,'score':v} for v,s,t,c in scored[:limit]]


def status():
    with connection() as conn:
        count=conn.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
        source_count=conn.execute('SELECT source, COUNT(*) FROM entries GROUP BY source').fetchall()
    return {'items':count,'sources':dict(source_count),'sync_running':STATE['running'],
            'last_completed':STATE['last_completed'],'warnings':STATE['last_error'],
            'sync_interval_seconds':INTERVAL}


def background_sync(stop_event):
    sync(include_remote=True)
    while not stop_event.wait(INTERVAL):sync(include_remote=True)


# Structured catalogue retrieval: a 'list all courses' question must never rely
# on top-k free-text RAG results.
def catalogue_titles():
    with connection() as con:
        rows=con.execute("SELECT title, content FROM entries WHERE source IN ('google_sheets:course_catalogue', 'google_sheets:registration_catalogue') ORDER BY id").fetchall()
    names=[]
    seen=set()
    for title, content in rows:
        if title.startswith('Course catalogue • '):
            name=title.split(' • ',1)[-1].strip()
        elif title.startswith('Registration course option • '):
            name=title.split(' • ',1)[-1].strip()
        else:
            continue
        key=re.sub(r'[^a-z0-9]+','',name.casefold())
        if name and key not in seen:
            seen.add(key);names.append(name)
    return names[:35]
