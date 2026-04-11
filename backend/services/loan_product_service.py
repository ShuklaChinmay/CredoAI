from fastapi import HTTPException
from bson import ObjectId
from database import db

product_collection = db["loan_products"]


class LoanProductService:

    def list_active(self):
        return list(product_collection.find({"is_active": True}, {"_id": 0}))

    def list_all(self):
        return list(product_collection.find({}, {"_id": 0}))

    def get_by_id(self, product_id: str):
        product = product_collection.find_one({"_id": ObjectId(product_id)})

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product["_id"] = str(product["_id"])
        return product

    def create(self, data: dict):
        result = product_collection.insert_one(data)
        return {"id": str(result.inserted_id)}

    def update(self, product_id: str, data: dict):
        result = product_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"message": "Updated"}

    def toggle_active(self, product_id: str):
        product = product_collection.find_one({"_id": ObjectId(product_id)})

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        new_status = not product.get("is_active", True)

        product_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"is_active": new_status}}
        )

        return {"is_active": new_status}

    def delete(self, product_id: str):
        result = product_collection.delete_one({"_id": ObjectId(product_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"message": "Deleted"}


loan_product_service = LoanProductService()