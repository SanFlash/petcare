import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY=os.getenv('SECRET_KEY','dev-secret-change-me')
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY','dev-jwt-change-me')
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///petcare-dev.db').replace('postgres://','postgresql://',1)
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    MAX_CONTENT_LENGTH=int(os.getenv('MAX_UPLOAD_MB','10'))*1024*1024
    JWT_TOKEN_LOCATION=['cookies']; JWT_COOKIE_SECURE=os.getenv('FLASK_ENV')=='production'; JWT_COOKIE_HTTPONLY=True; JWT_COOKIE_SAMESITE='Lax'
    JWT_ACCESS_TOKEN_EXPIRES=60*60*8
    RATELIMIT_STORAGE_URI=os.getenv('RATELIMIT_STORAGE_URI','memory://')
    SUPABASE_URL=os.getenv('SUPABASE_URL',''); SUPABASE_KEY=os.getenv('SUPABASE_KEY',''); SUPABASE_STORAGE_BUCKET=os.getenv('SUPABASE_STORAGE_BUCKET','petcare')
    APP_BASE_URL=os.getenv('APP_BASE_URL','http://localhost:5000')
