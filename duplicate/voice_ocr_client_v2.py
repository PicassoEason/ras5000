import os
import azure.cognitiveservices.speech as speechsdk
import requests
import pyaudio
import wave
import pygame
import subprocess
from datetime import datetime
import time

class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5
        
        # Ensure temporary directories exist
        self.temp_dir = "temp_files"
        self.image_dir = "image/temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        
    def record_audio(self, output_filename):
        """
        Record audio from microphone and save to file
        Args:
            output_filename: Name of the output WAV file
        Returns:
            str: Path to the saved audio file
        """
        output_path = os.path.join(self.temp_dir, output_filename)
        
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
        """Initialize with image directory setup"""
        self.image_dir = 'image/temp'
        os.makedirs(self.image_dir, exist_ok=True)
        
    def capture_image(self):
        """
        Capture image using libcamera-still
        Returns:
            str: Path to the captured image file, or None if capture fails
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.image_dir, f'capture_{timestamp}.jpg')
            
            # Use libcamera-still to capture image
            print("Press Enter to capture an image...")
            input()
            
            command = [
                'libcamera-still',
                '-o', filename,
                '--width', '1920',
                '--height', '1080',
                '--immediate'
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(filename):
                print(f"Image captured and saved as: {filename}")
                return filename
            else:
                print("Error capturing image:")
                print(result.stderr)
                return None
                
        except Exception as e:
            print(f"Error capturing image: {str(e)}")
            return None

def play_audio(filename):
    """
    Play audio file using pygame
    Args:
        filename: Path to the audio file to play
    """
    if not os.path.exists(filename):
        print(f"Audio file not found: {filename}")
        return
        
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
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
            str: Path to response audio file, or None if request fails
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
                response_path = os.path.join('temp_files', "response.wav")
                with open(response_path, "wb") as f:
                    f.write(response.content)
                return response_path
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None
        finally:
            for f in files.values():
                f[1].close()

    def send_ocr_query(self, image_file, audio_file):
        """
        Send image and audio to OCR Image and Audio API
        Args:
            image_file: Path to the image file
            audio_file: Path to the audio file
        Returns:
            str: Path to response audio file, or None if request fails
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
                response_path = os.path.join('temp_files', "ocr_response.wav")
                with open(response_path, "wb") as f:
                    f.write(response.content)
                return response_path
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None
        finally:
            for f in files.values():
                f[1].close()

def main():
    # Initialize components
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
            image_path = camera.capture_image()
            
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
            
    print("Program ended")

if __name__ == "__main__":
    main()