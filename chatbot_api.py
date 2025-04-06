from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from chat_bot import handle_user_query

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory user storage (Replace with database in production)
users = {}

# ====================
# Models
# ====================

class Query(BaseModel):
    query: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# ====================
# Routes
# ====================

@app.post("/ask")
async def ask_question(query: Query):
    response = handle_user_query(query.query)
    
    # If the response is a DataFrame or dict of DataFrames, convert to JSON
    if hasattr(response, 'to_dict'):
        return response.to_dict(orient='records')
    elif isinstance(response, dict):
        return {k: v.to_dict(orient='records') for k, v in response.items()}
    else:
        return {"response": response}


@app.post("/register")
async def register(user: UserRegister):
    if user.email in users:
        return {"error": "Email already registered."}
    
    users[user.email] = {
        "name": user.name,
        "email": user.email,
        "password": user.password  # In production, hash the password!
    }
    return {"message": "User registered successfully!"}


@app.post("/login")
async def login(user: UserLogin):
    stored_user = users.get(user.email)
    if not stored_user or stored_user["password"] != user.password:
        return {"error": "Invalid email or password"}
    
    return {"message": "Login successful!", "user": {"name": stored_user["name"], "email": stored_user["email"]}}

# ====================
# HTML Page Routes
# ====================

BASE_DIR = Path(__file__).resolve().parent

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    return FileResponse(BASE_DIR / "login.html")

@app.get("/signup", response_class=HTMLResponse)
async def serve_signup():
    return FileResponse(BASE_DIR / "signup.html")
