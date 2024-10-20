#  AI Speech Assistant

This project demonstrates how to set up an AI Assistant using Python, Twilio Voice with Media Streams, and OpenAI's Realtime API. It enables real-time voice interaction between the caller and the AI by exchanging audio data over WebSockets.

The application establishes WebSocket connections with both Twilio and OpenAI's Realtime API, facilitating a two-way voice conversation.

This project makes use of the following Twilio services in combination with OpenAI’s Realtime API:
- Twilio Voice (including TwiML and Media Streams)
- Twilio Phone Numbers

## Prerequisites

To get started, ensure you have the following:

- **Python 3.9+** 
- **A Twilio account.** You can sign up for a free trial [here](https://www.twilio.com/try-twilio).
- **A Twilio number with _Voice_ capabilities.** [Here are instructions](https://help.twilio.com/articles/223135247-How-to-Search-for-and-Buy-a-Twilio-Phone-Number-from-Console) to purchase a phone number.
- **An OpenAI account and an OpenAI API Key.** You can sign up [here](https://platform.openai.com/).
  - **OpenAI Realtime API access.**

## Local Setup

To run the app locally, follow these steps:
1. Set up a tunneling solution like ngrok to expose your local server for testing. Download ngrok [here](https://ngrok.com/).
2. (Optional) Create and activate a virtual environment for Python.
3. Install the necessary Python packages.
4. Configure Twilio settings.
5. Set up the .env file with your API credentials.

### Open an ngrok tunnel
When developing & testing locally, you'll need to open a tunnel to forward requests to your local development server. These instructions use ngrok.

Open a Terminal and run:
```
ngrok http 5050
```
This will provide a forwarding URL, such as https://[your-ngrok-subdomain].ngrok.app, which you'll need later when configuring Twilio. Make sure to use the correct port (5050 by default). If you modify the app’s port, adjust the ngrok command to match.

Note: Each time you start ngrok, a new forwarding URL is generated. You’ll need to update this URL in your Twilio settings whenever it changes.

### Install required packages

In the terminal (with the virtual environment, if you set it up) run:
```
pip install -r requirements.txt
```

### Twilio setup

#### Point a Phone Number to your ngrok URL
In the [Twilio Console](https://console.twilio.com/), go to **Phone Numbers** > **Manage** > **Active Numbers** and click on the additional phone number you purchased for this app in the **Prerequisites**.

In your Phone Number configuration settings, update the first **A call comes in** dropdown to **Webhook**, and paste your ngrok forwarding URL (referenced above), followed by `/incoming-call`. For example, `https://[your-ngrok-subdomain].ngrok.app/incoming-call`. Then, click **Save configuration**.

### Update the .env file

Create a `/env` file, or copy the `.env.example` file to `.env`:

```
cp .env.example .env
```

In the .env file, update the `OPENAI_API_KEY` to your OpenAI API key from the **Prerequisites**.

## Run the app
Once ngrok is running, dependencies are installed, Twilio is configured properly, and the `.env` is set up, run the dev server with the following command:
```
python main.py
```
## Test the app
With the development server running, call the phone number you purchased in the **Prerequisites**. After the introduction, you should be able to talk to the AI Assistant. Have fun!
