from datetime import datetime
from fastapi import HTTPException
from bson import ObjectId
from database import db

loan_collection = db["loans"]
doc_collection = db["documents"]


class LoanService:

    def create_application(self, user_id: str, data: dict):
        loan = {
            "user_id": user_id,
            "loan_type": data.get("loan_type", "personal"),
            "requested_amount": float(data.get("requested_amount", 0)),
            "purpose": data.get("purpose"),
            "status": "initiated",
            "created_at": datetime.utcnow()
        }

        result = loan_collection.insert_one(loan)
        loan["_id"] = str(result.inserted_id)
        return loan

    def get_user_applications(self, user_id: str):
        apps = list(loan_collection.find({"user_id": user_id}))

        for app in apps:
            app["_id"] = str(app["_id"])

        return apps

    def get_all_applications(self):
        apps = list(loan_collection.find())

        for app in apps:
            app["_id"] = str(app["_id"])

        return apps

    def get_by_id(self, loan_id: str):
        loan = loan_collection.find_one({"_id": ObjectId(loan_id)})

        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        loan["_id"] = str(loan["_id"])
        return loan

    def update_status(self, loan_id: str, status: str, reason: str = ""):
        result = loan_collection.update_one(
            {"_id": ObjectId(loan_id)},
            {"$set": {"status": status, "reason": reason}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Loan not found")

        return {"message": "Status updated"}


loan_service = LoanService()