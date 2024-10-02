from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import requests
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
load_dotenv()

app = Flask(__name__)

# Set up your API Keys and Twilio credentials
TWILIO_ACCOUNT_SID =('AC409a7533ffc6ebdcb913b1c23a724134')
TWILIO_AUTH_TOKEN =('5494ab062244a89596addad56078859f')
TWILIO_PHONE_NUMBER =('+18706003320')
DEEPGRAM_API_KEY =('6ba1567f417ee4c0d37dd31306ada2b31ae9db86')
OPENAI_API_KEY =('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')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Twilio webhook calls."""
    recording_url = request.form.get('RecordingUrl')

    if recording_url:
        # Twilio provides audio URL without an extension, so append `.wav`
        audio_url = f"{recording_url}.wav"
        
        # Step 1: Transcribe the audio with Deepgram
        transcript = transcribe_audio(audio_url)
        if transcript:
            # Step 2: Process the transcription with OpenAI GPT
            gpt_response = process_with_gpt(transcript)
            # Step 3: Convert GPT response to speech using Deepgram
            spoken_response_url = convert_text_to_speech(gpt_response)

            # Step 4: Create Twilio VoiceResponse to play the spoken response
            response = VoiceResponse()
            response.play(spoken_response_url)
            return str(response)

    return jsonify({"error": "Invalid request"}), 400

def transcribe_audio(audio_url):
    """Transcribe audio using Deepgram."""
    headers = {
        'Authorization': f'Token {DEEPGRAM_API_KEY}',
    }
    data = {
        'url': audio_url,
        'punctuate': True
    }
    response = requests.post(DEEPGRAM_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        transcript = response.json()['results']['channels'][0]['alternatives'][0]['transcript']
        return transcript
    return None

def process_with_gpt(transcript):
    """Send the transcription to OpenAI GPT for processing."""
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Respond to this: {transcript}",
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {e}"

def convert_text_to_speech(text):
    """Convert the GPT response to speech using Deepgram."""
    headers = {
        'Authorization': f'Token {DEEPGRAM_API_KEY}',
    }
    data = {
        'text': text,
        'voice': 'en-US'  # Specify the language and voice model
    }
    response = requests.post("https://api.deepgram.com/v1/speak", headers=headers, json=data)
    
    if response.status_code == 200:
        audio_url = response.json()['url']
        return audio_url
    return None

@app.route('/', methods=['GET'])
def home():
    return "Called GPT Backend is running!"

if __name__ == '__main__':
    app.run(debug=True)
