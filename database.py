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
        "name": "John",
        "email": "john.doe@example.com",
        "phone": "+123456789",
        "role": "customer",
        "account_status": "active"
    },
    {
        "_id": ObjectId(),
        "name": "Jane",
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
        "content": (
            "The Telco System Guide provides a comprehensive overview of the telecommunication "
            "system's architecture, including hardware components, software configurations, "
            "and network setup. It covers topics such as:\n\n"
            "1. **Core Network Infrastructure:** Explanation of switches, routers, and modems.\n"
            "2. **Software Systems:** Details on billing systems, CRM, and network monitoring.\n"
            "3. **Integration Guidelines:** How different systems interact within the architecture.\n"
            "4. **Common Workflows:** Description of daily operations and troubleshooting steps.\n"
            "5. **Support Process Overview:** Guidelines on handling service requests and issues."
        ),
        "created_at": "2023-09-15"
    },
    {
        "_id": ObjectId(),
        "title": "Troubleshooting Guide",
        "description": "How to troubleshoot common telco issues.",
        "content": (
            "The Troubleshooting Guide helps technicians resolve common telecommunication problems. "
            "It includes step-by-step instructions for:\n\n"
            "1. **Network Connectivity Issues:** Solutions for when devices can't connect to the network.\n"
            "   - Restart the modem and router.\n"
            "   - Check cable connections.\n"
            "   - Verify IP settings and DNS configurations.\n"
            "2. **VoIP Problems:** Fixes for call quality and connectivity issues.\n"
            "   - Ensure proper SIP configuration.\n"
            "   - Check bandwidth and network latency.\n"
            "3. **Slow Internet Speeds:** Methods to improve performance.\n"
            "   - Restart devices.\n"
            "   - Limit the number of connected devices.\n"
            "4. **Hardware Failures:** Steps for diagnosing and replacing faulty equipment."
        ),
        "created_at": "2023-10-01"
    },
    {
        "_id": ObjectId(),
        "title": "Network Configuration Manual",
        "description": "Guide on configuring network settings for different types of devices.",
        "content": (
            "The Network Configuration Manual covers how to set up network settings for various devices "
            "including routers, switches, and end-user devices. Topics include:\n\n"
            "1. **Router Configuration:** Setting up static IPs, DHCP, and port forwarding.\n"
            "2. **Switch Setup:** VLAN configuration and link aggregation.\n"
            "3. **Firewall Settings:** How to configure firewall rules for security.\n"
            "4. **Device-Specific Configurations:** Network settings for smart devices, printers, and servers.\n"
            "5. **Troubleshooting Tips:** Addressing common configuration issues."
        ),
        "created_at": "2023-08-20"
    },
    {
        "_id": ObjectId(),
        "title": "Security Best Practices",
        "description": "Recommendations for securing the telco system.",
        "content": (
            "This manual outlines the best practices for securing the telecommunication system to protect "
            "data and ensure network integrity. Recommendations include:\n\n"
            "1. **Using Firewalls:** Setting up perimeter and internal firewalls.\n"
            "2. **Encryption:** Implementing encryption for data in transit and at rest.\n"
            "3. **Software Updates:** Regularly applying security patches and updates.\n"
            "4. **User Access Control:** Enforcing strong password policies and multi-factor authentication.\n"
            "5. **Monitoring and Alerts:** Setting up systems to detect and alert on suspicious activities."
        ),
        "created_at": "2023-07-10"
    },
    {
        "_id": ObjectId(),
        "title": "VoIP Configuration Guide",
        "description": "Instructions for setting up VoIP services.",
        "content": (
            "The VoIP Configuration Guide provides instructions for setting up and maintaining VoIP services, "
            "including call quality optimization. Topics include:\n\n"
            "1. **SIP Trunk Configuration:** How to set up SIP trunks for inbound and outbound calls.\n"
            "2. **Codec Settings:** Choosing the right codec for your network conditions.\n"
            "3. **Quality of Service (QoS):** Ensuring call quality by prioritizing VoIP traffic.\n"
            "4. **VoIP Security:** Protecting against threats such as toll fraud and eavesdropping.\n"
            "5. **Troubleshooting VoIP Issues:** Identifying and resolving common VoIP problems."
        ),
        "created_at": "2023-06-05"
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
