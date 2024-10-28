import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)

# Define the database and collections
db = client["ai_assistant"]
users_collection = db["users"]
tickets_collection = db["tickets"]
manuals_collection = db["manuals"]
workflow_collection = db["workflow"]
call_record_collection = db['call_records']

# Dummy data for calling records
dummy_call_records = [
    {
        "call_id": 1,
        "phone_number": "+60123456789",
        "call_duration": 320,  # duration in seconds
        "call_time": datetime.now(),
        "caller_name": "John Doe",
    },
    {
        "call_id": 2,
        "phone_number": "+60198765432",
        "call_duration": 600,  # duration in seconds
        "call_time": datetime.now(),
        "caller_name": "Jane Smith",
    }
]

# Insert dummy call record data into the collection
call_record_collection.insert_many(dummy_call_records)

# Insert dummy data into 'users' collection
users = [
    {
        "_id": ObjectId(),
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+123456789",
        "role": "customer",
        "account_status": "active"
    },
    {
        "_id": ObjectId(),
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+987654321",
        "role": "support",
        "account_status": "active"
    }
]
users_collection.insert_many(users)

# Insert dummy data into 'tickets' collection
tickets = [
    {
        "_id": ObjectId(),
        "user_id": users[0]["_id"],
        "description": "Internet connection is slow.",
        "status": "open",
        "created_at": "2024-10-22",
        "assigned_to": users[1]["_id"]
    },
    {
        "_id": ObjectId(),
        "user_id": users[0]["_id"],
        "description": "Unable to make international calls.",
        "status": "resolved",
        "created_at": "2024-10-21",
        "assigned_to": users[1]["_id"]
    }
]
tickets_collection.insert_many(tickets)

# Insert dummy data into 'manuals' collection
manuals = [
    {
        "_id": ObjectId(),
        "title": "Telco System Guide",
        "description": "Overview of the telco system architecture.",
        "content": "This manual explains the basic telco system setup...",
        "created_at": "2023-09-15"
    },
    {
        "_id": ObjectId(),
        "title": "Troubleshooting Guide",
        "description": "How to troubleshoot common telco issues.",
        "content": "If you encounter network issues, follow these steps...",
        "created_at": "2023-10-01"
    }
]
manuals_collection.insert_many(manuals)

# Insert dummy data into 'workflow' collection (AI assistant functions and prompts)
workflow = [
    {
        "_id": ObjectId(),
        "function_name": "update_ticket",
        "description": "Updates a ticket based on user input.",
        "parameters": ["ticket_id", "description"],
        "example_prompt": "Update ticket #12345 with the following description: 'Fixed the internet speed issue.'"
    },
    {
        "_id": ObjectId(),
        "function_name": "get_user_data",
        "description": "Retrieve user data from the database.",
        "parameters": ["user_id"],
        "example_prompt": "Get the details of user with ID #987654321."
    },
    {
        "_id": ObjectId(),
        "function_name": "get_system_manual",
        "description": "Retrieve system manual information for telco.",
        "parameters": ["manual_id"],
        "example_prompt": "Retrieve the system manual titled 'Telco System Guide'."
    }
]
workflow_collection.insert_many(workflow)

print("Database setup complete with dummy data.")
