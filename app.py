from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import moviepy.editor as mp
import speech_recognition as sr
from gtts import gTTS
import re

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Extract audio from video
        audio_path = os.path.join(UPLOAD_FOLDER, "extracted_audio.wav")
        video_clip = mp.VideoFileClip(file_path)
        video_clip.audio.write_audiofile(audio_path)

        # Transcribe audio
        transcription = transcribe_audio(audio_path)

        # Correct transcription using basic Python functions
        corrected_transcription = correct_transcription(transcription)

        # Synthesize corrected audio
        new_audio_path = os.path.join(PROCESSED_FOLDER, "new_audio.wav")
        synthesize_text(corrected_transcription, new_audio_path)

        # Replace audio in video
        output_video_path = os.path.join(PROCESSED_FOLDER, "final_output.mp4")
        replace_audio_in_video(file_path, new_audio_path, output_video_path)

        return send_file(output_video_path, as_attachment=True, download_name="final_output.mp4")

# Speech-to-text using SpeechRecognition library
def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        try:
            transcription = recognizer.recognize_google(audio)
            return transcription
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError:
            return "Could not request results from the Speech Recognition service."

# Correct transcription using Python functions
def correct_transcription(transcription):
    # Simple grammar and filler words removal
    cleaned_transcription = re.sub(r'\b(uh|um|hmm|like|you know)\b', '', transcription, flags=re.IGNORECASE)
    cleaned_transcription = re.sub(r'\s+', ' ', cleaned_transcription).strip()
    return cleaned_transcription.capitalize() + '.'

# Synthesize text using gTTS
def synthesize_text(text, output_audio_file):
    tts = gTTS(text=text, lang='en')
    tts.save(output_audio_file)

# Replace original audio with synthesized audio
def replace_audio_in_video(video_file, new_audio_file, output_file):
    video_clip = mp.VideoFileClip(video_file)
    new_audio = mp.AudioFileClip(new_audio_file)

    # Trim video if it’s longer than audio
    audio_duration = new_audio.duration
    video_clip = video_clip.subclip(0, audio_duration)

    final_video = video_clip.set_audio(new_audio)
    final_video.write_videofile(output_file, codec="libx264", audio_codec="aac")

if __name__ == '__main__':
    app.run(debug=True)
