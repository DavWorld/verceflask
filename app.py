import os
import time
import threading
import pyaudio
import wave
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from flask import Flask, render_template, request

# Constants
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORDING_DURATION = 7  # 7 seconds
UPLOAD_INTERVAL = 30  # 30 seconds

# Get the directory where the current script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to your client secret file
client_secret_file = os.path.join(script_directory, 'patchtoGOOGLEDRIVE.json')

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
creds = None

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
        creds = flow.run_local_server(port=0)

    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('drive', 'v3', credentials=creds)

# Define the folder ID where you want to store the audio files
folder_id = '1EP-3A03kZzN59pwOUU7oJHmggVrvtgTA'  # Replace with your folder ID

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'XeWYp4RajRHSwziJLNnSATZ55w8MfCpK'  # Replace with your own secret key

# Function to start and stop recording based on user actions
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record', methods=['POST'])
def record():
    if request.form['action'] == 'start':
        threading.Thread(target=record_and_upload).start()
        return 'Recording started'
    elif request.form['action'] == 'stop':
        return 'Recording stopped and uploaded'

# Function for recording and uploading
def record_and_upload():
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    try:
        start_time = time.time()
        while time.time() - start_time < RECORDING_DURATION:
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    audio_filename = f"recorded_{int(time.time())}.wav"
    with wave.open(audio_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    # Close the audio file explicitly
    wf.close()

    # Upload the audio file to your Google Drive folder
    file_metadata = {
        'name': audio_filename,
        'mimeType': 'audio/wav',
        'parents': [folder_id]
    }
    media = MediaFileUpload(audio_filename, mimetype='audio/wav')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    # Remove the temporary audio file after it's closed
    os.remove(audio_filename)


if __name__ == "__main__":
    app.run(debug=True)