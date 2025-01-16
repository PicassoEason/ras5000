import requests
import pyaudio
import wave
import pygame
import cv2
import numpy as np
from PIL import Image
import io
import time
import os

# Define directory for temporary files
TEMP_DIR = "temp_files"

class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5  # Recording duration in seconds
        
        # Ensure temporary directory exists
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)
        
    def record_audio(self, output_filename):
        """
        Record audio from microphone and save to file
        Args:
            output_filename: Name of the output WAV file
        Returns:
            str: Path to the saved audio file
        """
        # Ensure using full path
        output_path = os.path.join(TEMP_DIR, output_filename)
        
        p = pyaudio.PyAudio()
        
        stream = p.open(format=self.FORMAT,
                       channels=self.CHANNELS,
                       rate=self.RATE,
                       input=True,
                       frames_per_buffer=self.CHUNK)
        
        print("* recording")
        frames = []
        
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            frames.append(data)
        
        print("* done recording")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return output_path

class CameraCapture:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)  # Initialize camera (0 is usually the built-in camera)
        
        # Ensure temporary directory exists
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)
        
    def capture_image(self, output_filename):
        """
        Capture image from camera and save to file
        Args:
            output_filename: Name of the output image file
        Returns:
            str: Path to the saved image file, or None if capture fails
        """
        output_path = os.path.join(TEMP_DIR, output_filename)
        
        ret, frame = self.camera.read()
        if ret:
            cv2.imwrite(output_path, frame)
            print(f"Image saved to {output_path}")
            return output_path
        return None
    
    def release(self):
        """Release the camera resource"""
        self.camera.release()

def play_audio(filename):
    """
    Play audio file using pygame
    Args:
        filename: Name of the audio file to play
    """
    audio_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        return
        
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

class APIClient:
    def __init__(self, base_url="http://192.168.100.233:3100"):
        self.base_url = base_url
        
    def send_voice_query(self, audio_file):
        """
        Send voice query to RAG Voice Assistant API
        Args:
            audio_file: Path to the audio file
        Returns:
            str: Filename of response audio, or None if request fails
        """
        url = f"{self.base_url}/rag-voice-assistant"
        
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return None
            
        files = {'file': ('query.wav', open(audio_file, 'rb'), 'audio/wav')}
        
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                # Save response audio
                response_path = os.path.join(TEMP_DIR, "response.wav")
                with open(response_path, "wb") as f:
                    f.write(response.content)
                return "response.wav"
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None
        finally:
            # Close files
            for f in files.values():
                f[1].close()

    def send_ocr_query(self, image_file, audio_file):
        """
        Send image and audio to OCR Image and Audio API
        Args:
            image_file: Path to the image file
            audio_file: Path to the audio file
        Returns:
            str: Filename of response audio, or None if request fails
        """
        url = f"{self.base_url}/process-ocr-image-and-audio"
        
        # Check if files exist
        if not os.path.exists(image_file):
            print(f"Image file not found: {image_file}")
            return None
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return None
            
        files = {
            'image': ('image.jpg', open(image_file, 'rb'), 'image/jpeg'),
            'audio': ('query.wav', open(audio_file, 'rb'), 'audio/wav')
        }
        
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                # Save response audio
                response_path = os.path.join(TEMP_DIR, "ocr_response.wav")
                with open(response_path, "wb") as f:
                    f.write(response.content)
                return "ocr_response.wav"
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None
        finally:
            # Close files
            for f in files.values():
                f[1].close()

def main():
    # Initialize required classes
    recorder = AudioRecorder()
    camera = CameraCapture()
    api_client = APIClient()  # Remember to change to your server URL
    
    while True:
        print("\n1. Voice Query")
        print("2. OCR + Voice Query")
        print("3. Exit")
        choice = input("Choose option (1-3): ")
        
        if choice == "1":
            # Voice query only
            print("Press Enter to start recording...")
            input()
            audio_path = recorder.record_audio("query.wav")
            
            print("Sending request to server...")
            response_file = api_client.send_voice_query(audio_path)
            
            if response_file:
                print("Playing response...")
                play_audio(response_file)
                
        elif choice == "2":
            # OCR + Voice query
            print("Taking photo...")
            image_path = camera.capture_image("image.jpg")
            
            if image_path:
                print("Press Enter to start recording...")
                input()
                audio_path = recorder.record_audio("query.wav")
                
                print("Sending request to server...")
                response_file = api_client.send_ocr_query(image_path, audio_path)
                
                if response_file:
                    print("Playing response...")
                    play_audio(response_file)
            else:
                print("Failed to capture image!")
                
        elif choice == "3":
            break
            
    camera.release()
    print("Program ended")

if __name__ == "__main__":
    main()