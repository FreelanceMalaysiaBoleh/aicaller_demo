import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request,HTTPException
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv

from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from twilio.rest import Client

# Load Twilio credentials from .env
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

# Initialize Twilio REST client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Load environment variables from a .env file
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)

# Define the database and collections
db = client["ai_assistant"]
users_collection = db["users"]
tickets_collection = db["tickets"]
manuals_collection = db["manuals"]
workflow_collection = db["workflow"]
call_record_collection = db['call_records']

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Requires OpenAI Realtime API Access
PORT = int(os.getenv('PORT', 5050))

# System message that sets the behavior of the assistant
SYSTEM_MESSAGE = (
    "You are a helpful and knowledgeable AI assistant. "
    "You can use provided tools to assist the user when necessary. "
    "If you use a tool, wait for the result before responding to the user. "
    "Always provide clear and concise information."
)

# Voice configuration for the assistant
VOICE = 'alloy'

# Event types to log from the OpenAI Realtime API
LOG_EVENT_TYPES = [
    'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created',
    'response.function_call_arguments.delta', 'response.function_call_arguments.done',
    'response.function_call_arguments.failed'
]

# Initialize FastAPI app
app = FastAPI()

# Ensure the OpenAI API key is provided
if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')


async def save_call_record(phone_number: str, call_duration: float, call_time: datetime):
    """
    Save the call record to MongoDB.
    :param phone_number: The caller's phone number.
    :param call_duration: Duration of the call in seconds.
    :param call_time: Timestamp when the call started.
    """
    try:
        call_record = {
            "phone_number": phone_number,
            "call_duration": call_duration,  # Duration in seconds
            "call_time": call_time  # Timestamp of when the call started
        }
        call_record_collection.insert_one(call_record)
        print(f"Call record saved: {call_record}")
    except Exception as e:
        print(f"Error saving call record: {e}")

@app.get("/", response_class=HTMLResponse)
async def index_page():
    """
    Handle the root URL and return a simple message.
    """
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """
    Handle incoming calls and return TwiML response to connect to Media Stream.
    """
    response = VoiceResponse()
    # Provide introductory messages to the caller
    response.say("Please wait while we connect your call to the AI voice assistant, powered by Twilio and the OpenAI Realtime API.")
    response.pause(length=1)
    response.say("OK, you can start talking!")
    host = request.url.hostname
    # Create a Connect verb to stream the call via WebSocket
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    # Return the TwiML response
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """
    Handle WebSocket connections between Twilio and OpenAI.
    This function establishes a connection with the OpenAI Realtime API and manages the data exchange.
    """
    print("Client connected")
    await websocket.accept()

    # Connect to OpenAI Realtime API via WebSocket
    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        # Send session update to configure the assistant
        await send_session_update(openai_ws)
        stream_sid = None  # Stream SID from Twilio

        # Variables to keep track of function calls
        function_call_id = None
        function_name = None

        # Variables for call metadata
        call_start_time = None
        call_end_time = None
        phone_number = None

        async def receive_from_twilio():
            """
            Receive audio data from Twilio and send it to the OpenAI Realtime API.
            """
            nonlocal stream_sid, call_start_time, call_end_time, phone_number
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    print(data)
                    event = data.get('event')

                    if event == 'media' and openai_ws.open:
                        # Append audio data to the OpenAI input buffer
                        audio_payload = data['media']['payload']
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": audio_payload
                        }
                        await openai_ws.send(json.dumps(audio_append))

                    elif event == 'start':
                        # Capture call start time and callSid
                        stream_sid = data.get('start', {}).get('streamSid')
                        call_sid = data.get('start', {}).get('callSid')
                        call_start_time = datetime.utcnow()
                        print(f"Incoming stream has started {stream_sid} with Call SID {call_sid}")

                        # Fetch caller's phone number using Twilio REST API
                        try:
                            call = twilio_client.calls(call_sid).fetch()
                            phone_number = call._from  # Use _from instead of from_
                            print(f"Caller Phone Number: {phone_number}")
                        except Exception as e:
                            phone_number = "Unknown"
                            print(f"Error fetching call details: {e}")

                    elif event == 'stop':
                        # Capture call end time and calculate duration
                        call_end_time = datetime.utcnow()
                        if call_start_time:
                            call_duration = (call_end_time - call_start_time).total_seconds()
                        else:
                            call_duration = 0
                        print(f"Incoming stream has ended {stream_sid}. Duration: {call_duration} seconds")

                        # Save call record to the database
                        await save_call_record(phone_number, call_duration, call_start_time)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

                # Calculate call duration upon disconnection if not already done
                call_end_time = datetime.utcnow()
                if call_start_time:
                    call_duration = (call_end_time - call_start_time).total_seconds()
                else:
                    call_duration = 0
                print(f"WebSocket disconnected. Call Duration: {call_duration} seconds")

                # Save call record to the database
                await save_call_record(phone_number, call_duration, call_start_time)
            except Exception as e:
                print(f"Error in receive_from_twilio: {e}")

        async def send_to_twilio():
            """
            Receive events from the OpenAI Realtime API and send audio back to Twilio.
            """
            nonlocal stream_sid, function_call_id, function_name
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    event_type = response.get('type')
                    # Log specific events for debugging purposes
                    if event_type in LOG_EVENT_TYPES:
                        print(f"Received event: {event_type}", response)
                    if event_type == 'session.updated':
                        print("Session updated successfully.")
                    elif event_type == 'response.function_call_arguments.delta':
                        # Handle function call arguments being received in chunks
                        delta = response.get('delta', '')
                        function_call_id = response.get('call_id')
                        print(f"Function call delta received: {delta}")
                    elif event_type == 'response.function_call_arguments.done':
                        # Function call arguments have been fully received
                        print("Function call arguments received completely.")
                        # Extract call_id, function name, and arguments
                        function_call_id = response.get('call_id')
                        function_name = response.get('name')
                        function_arguments_str = response.get('arguments', '')
                        # Parse the arguments JSON string into a dictionary
                        try:
                            arguments = json.loads(function_arguments_str)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding function arguments: {e}")
                            function_result = {"error": "Invalid arguments."}
                        else:
                            # Execute the requested function
                            function_result = await execute_function(function_name, arguments)
                        # Send the function call output back to OpenAI
                        print(f"Function output: {function_result}")
                        function_call_output = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": function_call_id,
                                "output": function_result.get('result', '')
                            }
                        }
                        await openai_ws.send(json.dumps(function_call_output))
                        # Request the model to generate a new response
                        await openai_ws.send(json.dumps({"type": "response.create"}))
                        # Reset function call variables
                        function_call_id = None
                        function_name = None
                    elif event_type == 'response.audio.delta' and response.get('delta'):
                        # Receive audio data from OpenAI and send it to Twilio
                        try:
                            # Decode and re-encode the audio payload
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
                    elif event_type == 'error':
                        # Log any error events
                        print(f"Error event received: {response.get('error')}")
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        # Run both receive and send tasks concurrently
        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_session_update(openai_ws):
    """
    Send session update to OpenAI WebSocket with function definitions.
    This configures the assistant's behavior and available tools.
    """
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get the current weather for a given city.",
                    "type": "function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "Name of the city to get the weather for."
                            }
                        },
                        "required": ["city"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "create_ticket",
                    "description": "Create a new ticket based on user input. The user is identified by their name.",
                    "type": "function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_name": {
                                "type": "string",
                                "description": "Name of the user creating the ticket."
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the issue or request."
                            }
                        },
                        "required": ["user_name", "description"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "get_user_data",
                    "description": "Retrieve user data from the database.",
                    "type": "function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "ID of the user to retrieve."
                            }
                        },
                        "required": ["user_id"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "get_system_manual",
                    "description": "Retrieve system manual information for telco.",
                    "type": "function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "manual_id": {
                                "type": "string",
                                "description": "Manual ID to retrieve."
                            }
                        },
                        "required": ["manual_id"],
                        "additionalProperties": False
                    }
                }
            ]
        }
    }
    print('Sending session update.')
    await openai_ws.send(json.dumps(session_update))

async def execute_function(function_name, arguments):
    """
    Execute the called function based on the function name and provided arguments.
    """
    if function_name == 'get_weather':
        city = arguments.get('city')
        if city:
            result = get_weather(city)
            return {"result": result}
        else:
            return {"error": "City not provided."}

    elif function_name == 'create_ticket':
        user_name = arguments.get('user_name')
        description = arguments.get('description')

        if not user_name or not description:
            return {"error": "Both user_name and description are required."}

        # Call the create_ticket function
        return create_ticket(user_name, description)

    elif function_name == 'get_user_data':
        user_id = arguments.get('user_id')
        if user_id:
            result = get_user_data(user_id)
            return {"result": result}
        else:
            return {"error": "User ID not provided."}

    elif function_name == 'get_system_manual':
        manual_id = arguments.get('manual_id')
        if manual_id:
            result = get_system_manual(manual_id)
            return {"result": result}
        else:
            return {"error": "Manual ID not provided."}

    else:
        return {"error": f"Function {function_name} not implemented."}

def get_weather(city: str) -> str:
    """
    Placeholder function to get weather information for a city.
    In a real implementation, this would fetch data from a weather API.
    """
    weather_info = f"The current weather in {city} is sunny with a temperature of 25°C."
    return weather_info

def create_ticket(user_name: str, description: str) -> dict:
    """
    Create a new ticket for a user based on their name.
    :param user_name: The name of the user who is creating the ticket.
    :param description: The description of the issue or request.
    :return: A dictionary with the result of the ticket creation.
    """
    # Find the user by name in the users collection
    user = users_collection.find_one({"name": user_name})

    if not user:
        # Return an error if the user is not found
        return {"error": f"User with name {user_name} not found."}

    # Extract the user ID from the user document
    user_id = user["_id"]

    # Create a new ticket document
    ticket = {
        "user_id": user_id,
        "description": description,
        "status": "open",
        "created_at": datetime.now(),
        "assigned_to": None  # Assigned later if needed
    }

    # Insert the ticket into the tickets collection
    tickets_collection.insert_one(ticket)

    return {"result": f"Ticket created successfully for user {user_name}."}

def get_user_data(user_id: str) -> dict:
    """
    Retrieve user data by user_id.
    :param user_id: The ObjectId of the user as a string.
    :return: A dictionary containing user information or an error message.
    """
    try:
        # Convert the user_id string to an ObjectId
        user_object_id = ObjectId(user_id)
    except Exception as e:
        return {"error": "Invalid user ID format."}

    # Find the user in the users collection
    user = users_collection.find_one({"_id": user_object_id})
    if user:
        # Return user details
        return {
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"],
            "status": user["account_status"]
        }
    else:
        return {"error": "User not found."}

def get_system_manual(manual_id: str) -> dict:
    """
    Retrieve a system manual by manual_id.
    :param manual_id: The ObjectId of the manual as a string.
    :return: A dictionary containing manual information or an error message.
    """
    try:
        # Convert the manual_id string to an ObjectId
        manual_object_id = ObjectId(manual_id)
    except Exception as e:
        return {"error": "Invalid manual ID format."}

    # Find the manual in the manuals collection
    manual = manuals_collection.find_one({"_id": manual_object_id})
    if manual:
        # Return manual details
        return {
            "title": manual["title"],
            "description": manual["description"],
            "content": manual["content"]
        }
    else:
        return {"error": "Manual not found."}
    

# Endpoint to retrieve the list of tickets
@app.get("/api/tickets", response_model=list)
async def get_tickets():
    """
    Get the list of all tickets.
    Returns:
        List of tickets with details such as description, status, and user information.
    """
    try:
        # Fetch all tickets from the database
        tickets = list(tickets_collection.find())
        # Convert ObjectId to string for JSON serialization
        for ticket in tickets:
            ticket["_id"] = str(ticket["_id"])
            ticket["user_id"] = str(ticket["user_id"])
            if ticket.get("assigned_to"):
                ticket["assigned_to"] = str(ticket["assigned_to"])
        return JSONResponse(content=tickets)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching tickets.")

# Endpoint to retrieve the list of call records
@app.get("/api/call-records", response_model=list)
async def get_call_records():
    """
    Get the list of all call records.
    Returns:
        List of call records with details such as phone number, duration, and call time.
    """
    try:
        # Fetch all call records from the database
        call_records = list(call_record_collection.find())
        # Convert ObjectId to string and datetime to string for JSON serialization
        for call_record in call_records:
            if "_id" in call_record:
                call_record["_id"] = str(call_record["_id"])
            if "call_time" in call_record:
                call_record["call_time"] = call_record["call_time"].isoformat()  # Convert datetime to ISO format
        return JSONResponse(content=call_records)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching call records.")


if __name__ == "__main__":
    # Run the FastAPI app with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
