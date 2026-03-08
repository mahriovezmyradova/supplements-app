# audio_recorder.py
import streamlit as st
import numpy as np
import base64
import io
import wave
from streamlit.components.v1 import html

def audio_recorder():
    """Custom audio recorder component that returns audio data"""
    
    # Create a unique key for this instance
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None
    
    recorder_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .recorder-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .record-button {
                width: 140px;
                height: 140px;
                border-radius: 50%;
                border: none;
                background: linear-gradient(135deg, rgb(38, 96, 65), rgb(30, 76, 52), rgb(25, 63, 43));
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 20px 25px -5px rgba(38, 96, 65, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 3.5rem;
                margin: 0 auto 20px auto;
                color: white;
            }
            .record-button:hover {
                transform: scale(1.1);
                box-shadow: 0 25px 30px -5px rgba(38, 96, 65, 0.5);
            }
            .record-button.recording {
                background: linear-gradient(135deg, #fb923c, #ef4444, #ec4899);
                animation: pulse-glow 2s ease-in-out infinite;
            }
            @keyframes pulse-glow {
                0%, 100% {
                    box-shadow: 0 0 30px rgba(251, 146, 60, 0.6), 0 0 60px rgba(236, 72, 153, 0.4);
                }
                50% {
                    box-shadow: 0 0 50px rgba(251, 146, 60, 0.8), 0 0 90px rgba(236, 72, 153, 0.6);
                }
            }
            .timer {
                font-family: monospace;
                font-size: 1.5rem;
                color: #333;
                margin: 10px 0;
            }
            .status-text {
                color: #64748b;
                font-size: 1rem;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="recorder-container">
            <button id="recordButton" class="record-button">
                🎤
            </button>
            <div id="timer" class="timer">00:00</div>
            <div id="status" class="status-text">Klicken Sie auf das Mikrofon, um die Aufnahme zu starten</div>
        </div>

        <script>
            let mediaRecorder;
            let audioChunks = [];
            let isRecording = false;
            let startTime;
            let timerInterval;
            
            const recordButton = document.getElementById('recordButton');
            const timerDisplay = document.getElementById('timer');
            const statusDisplay = document.getElementById('status');
            
            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    
                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const reader = new FileReader();
                        
                        reader.onloadend = () => {
                            // Send the audio data back to Streamlit
                            const base64Audio = reader.result.split(',')[1];
                            window.parent.postMessage({
                                type: 'streamlit:audioRecorded',
                                audioData: base64Audio
                            }, '*');
                            statusDisplay.textContent = 'Aufnahme abgeschlossen!';
                        };
                        
                        reader.readAsDataURL(audioBlob);
                        
                        // Stop all tracks
                        stream.getTracks().forEach(track => track.stop());
                        audioChunks = [];
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    recordButton.classList.add('recording');
                    startTime = Date.now();
                    statusDisplay.textContent = '🔴 Aufnahme läuft...';
                    
                    timerInterval = setInterval(() => {
                        const elapsed = Math.floor((Date.now() - startTime) / 1000);
                        const minutes = Math.floor(elapsed / 60);
                        const seconds = elapsed % 60;
                        timerDisplay.textContent = 
                            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    }, 1000);
                    
                } catch (err) {
                    console.error('Error accessing microphone:', err);
                    statusDisplay.textContent = '❌ Mikrofon nicht verfügbar. Bitte erlauben Sie den Zugriff.';
                }
            }
            
            function stopRecording() {
                if (mediaRecorder && isRecording) {
                    mediaRecorder.stop();
                    isRecording = false;
                    recordButton.classList.remove('recording');
                    clearInterval(timerInterval);
                    timerDisplay.textContent = '00:00';
                }
            }
            
            recordButton.addEventListener('click', () => {
                if (!isRecording) {
                    startRecording();
                } else {
                    stopRecording();
                }
            });
            
            // Listen for messages from Streamlit
            window.addEventListener('message', (event) => {
                if (event.data.type === 'streamlit:stopRecording') {
                    stopRecording();
                }
            });
        </script>
    </body>
    </html>
    """
    
    # Display the recorder
    html(recorder_html, height=300)
    
    # Return the audio data from session state
    audio_data = st.session_state.get('audio_data', None)
    if audio_data:
        st.session_state.audio_data = None  # Clear after reading
        return base64.b64decode(audio_data)
    return None