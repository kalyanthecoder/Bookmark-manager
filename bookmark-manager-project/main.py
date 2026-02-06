from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import SessionLocal, User, Bookmark, Tag
from auth import create_access_token, verify_password, get_password_hash, get_current_user
import schemas

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    return {"message": "User created"}

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/bookmarks/")
def add_bookmark(bookmark: schemas.BookmarkBase, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_bm = Bookmark(title=bookmark.title, url=bookmark.url, notes=bookmark.notes, user_id=user.id)
    db.add(db_bm)
    for tag_name in bookmark.tags:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
        db_bm.tags.append(tag)
    db.commit()
    return db_bm

@app.get("/bookmarks/")
def get_bookmarks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Bookmark).filter(Bookmark.user_id == user.id).all()

@app.get("/search/")
def search_bookmarks(keyword: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Bookmark).filter(Bookmark.user_id == user.id, Bookmark.title.contains(keyword)).all()
