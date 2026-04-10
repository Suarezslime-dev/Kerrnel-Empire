import json
import os
from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
DB_FILE = "data.json"

# --- CONFIGURATION INITIALE ---
# Crée le dossier static s'il n'existe pas pour éviter les erreurs au démarrage
if not os.path.exists("static"):
    os.makedirs("static")

def load_db():
    if not os.path.exists(DB_FILE):
        return {"games": [], "stats": {"subs": 30, "views": 500}, "avatar": "/static/avatar.png"}
    with open(DB_FILE, "r", encoding="utf-8") as f: 
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- ROUTES PUBLIQUES ---

@app.get("/")
async def home():
    return FileResponse('index.html')

@app.get("/api/all")
async def get_data():
    db = load_db()
    db["stats"]["views"] += 1
    save_db(db)
    return db

@app.post("/api/subscribe")
async def subscribe():
    db = load_db()
    db["stats"]["subs"] += 1
    save_db(db)
    return {"new_subs": db["stats"]["subs"]}

# --- ROUTE SÉCURISÉE (LOGIN) ---

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <body style="background:#0a0a0c; color:white; text-align:center; padding:100px; font-family:sans-serif;">
        <form action="/admin" method="post" style="display:inline-block; background:#111; padding:40px; border:2px solid #ff4444; border-radius:15px;">
            <h2 style="font-family:sans-serif; letter-spacing:2px;">ACCÈS PROPRIO</h2>
            <input type="password" name="password" placeholder="Code d'accès" style="padding:12px; margin-bottom:20px; width:250px; border-radius:5px; border:1px solid #333;"><br>
            <button type="submit" style="background:#ff4444; color:white; border:none; padding:12px 30px; cursor:pointer; font-weight:bold; border-radius:5px;">ENTRER</button>
        </form>
    </body>
    """

@app.post("/admin")
async def check_admin(password: str = Form(...)):
    if password == "33-75-814":
        return FileResponse('admin.html')
    return HTMLResponse("<h1 style='color:red; text-align:center;'>Code incorrect !</h1>", status_code=401)

# --- MISE À JOUR (ADMIN) ---

@app.post("/admin/update")
async def update(
    game_name: str = Form(None), 
    game_url: str = Form(None), 
    avatar: UploadFile = File(None)
):
    db = load_db()
    
    # Ajout d'un jeu
    if game_name and game_url:
        db["games"].append({"name": game_name, "url": game_url})
    
    # Upload de l'image (l'image est enregistrée DIRECTEMENT dans static)
    if avatar and avatar.filename:
        file_path = f"static/{avatar.filename}"
        content = await avatar.read()
        with open(file_path, "wb") as f:
            f.write(content)
        db["avatar"] = f"/{file_path}" # On enregistre le chemin pour le HTML
    
    save_db(db)
    # On redirige vers l'accueil pour voir les changements
    return RedirectResponse(url="/", status_code=303)

# Montage du dossier static pour servir les images et builds
app.mount("/static", StaticFiles(directory="static"), name="static")