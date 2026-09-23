import os
import redis
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import Link, User
from .schema import ShortenIn, UserCreate,LoginUser
from .utility import base62
from argon2 import PasswordHasher
from .auth import create_token , get_current_user_id

Base.metadata.create_all(engine)
cache = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
app = FastAPI(title="URL Shortener")


@app.post("/links", status_code=201)
def create(body: ShortenIn, db: Session = Depends(get_db), user_id : int = Depends(get_current_user_id)):
      


    url = str(body.url).strip()
    link = Link(url=url, user_id =user_id)

    existing_link = db.execute(
    select(Link).where((Link.url == url) | (Link.user_id == user_id))
    ).scalar()
    if existing_link:
        raise HTTPException(400, "You've already shortened this URL")

    db.add(link)
    ##the flush methos is to push as tumporary not finalize to generate id and make the changes
    db.flush()                      

    link.code = base62(link.id)
    ### the commit is to finalize all changes 
    db.commit()
    return {"code": link.code, "short_url": f"http://localhost:8000/{link.code}"}


@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db), ):
        url = cache.get(f"url:{code}")
        if not url:
            url = db.scalar(select(Link.url).where(Link.code == code))
            if not url:
                raise HTTPException(404, "Not found")
            cache.set(f"url:{code}", url, ex=3600)
        db.execute(update(Link).where(Link.code == code).values(clicks=Link.clicks + 1))
        db.commit()
        return RedirectResponse(url, status_code=307)


@app.get("/links/all")
def list_all_links(db: Session = Depends(get_db), user_id : int = Depends(get_current_user_id)):

    

        
        links = db.execute(select(Link).where(Link.user_id == user_id)).scalars().all()

        return [{"code": link.code, "url": link.url, "clicks": link.clicks} for link in links]








@app.post("/sign_up",status_code=201)
def sign_up(body: UserCreate, db: Session = Depends(get_db)):

            ## no parametars 
        username = body.username
        email = body.email.strip().lower()
        password = body.password

        if not username or not email or not password:
            raise HTTPException(409, "Missing required fields")

        existing_user = db.execute(select(User).where((User.email == email) | (User.username == username))).scalar()
        if existing_user:
            raise HTTPException(409, "Email or username already exists")


        Hpassword = PasswordHasher().hash(password)

        user = User(username=username, email=email, password_hash=Hpassword)



        db.add(user)

        db.commit()

        db.refresh(user)
        return {"message": "User created successfully", "user": user.username,"access_token":create_token(user.id)}
        


@app.post("/login", status_code=200)
def login(body: LoginUser, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar()

    if not user:
        raise HTTPException(401, "Invalid credentials")

    try:
        PasswordHasher().verify(user.password_hash, body.password)
    except Exception:
        raise HTTPException(401, "Invalid credentials")

    return {"access_token": create_token(user.id)}


     









