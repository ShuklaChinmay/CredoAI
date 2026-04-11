from pymongo import MongoClient
from config.settings import settings

client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)

try:
    client.server_info()
    print("✅ MongoDB connected successfully")
except Exception as e:
    print("❌ MongoDB connection error:", e)

db = client["loanai_db"]

users_collection = db["users"]
loans_collection = db["loans"]
documents_collection = db["documents"]