import sys
from main import app, register
from schemas import UserCreate
from database import SessionLocal
import traceback

try:
    db = SessionLocal()
    user = UserCreate(username="test_script_user_1", email="testscript1@example.com", password="password", role="user")
    res = register(user=user, db=db)
    print(res)
except Exception as e:
    exc_info = sys.exc_info()
    traceback.print_exception(*exc_info)
