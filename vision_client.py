import os
import pyaudio
import wave
import subprocess
from datetime import datetime
import requests
import pygame
import time

class AudioRecorder:
    """Class to handle audio recording functionality"""
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5
        
        # Ensure temporary directory exists
        self.temp_dir = "temp_files"
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def record_audio(self, output_filename):
        """
        Record audio from microphone
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
    """Class to handle camera capture using libcamera-still"""
    def __init__(self):
        self.image_dir = 'image/temp'
        os.makedirs(self.image_dir, exist_ok=True)
        
    def capture_image(self):
        """
        Capture image using libcamera-still
        Returns:
            str: Path to the captured image file, or None if capture fails
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.image_dir, f'capture_{timestamp}.jpg')
            
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

class VisionAPIClient:
    def __init__(self, base_url="http://192.168.100.233:3100"):
        self.base_url = base_url
        
    def process_image_and_query(self, image_path, audio_path):
        """
        Send image and audio to process-text-and-image API
        Args:
            image_path: Path to the image file
            audio_path: Path to the audio file
        Returns:
            str: Path to response audio file, or None if request fails
        """
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return None
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return None

        url = f"{self.base_url}/process-text-and-image"
        
        try:
            with open(image_path, 'rb') as img_file, open(audio_path, 'rb') as audio_file:
                files = {
                    'image': ('image.jpg', img_file, 'image/jpeg'),
                    'audio': ('query.wav', audio_file, 'audio/wav')
                }
                
                print("Sending request to server...")
                response = requests.post(url, files=files)
                
                if response.status_code == 200:
                    # Save response audio
                    response_path = os.path.join('temp_files', "vision_response.wav")
                    with open(response_path, "wb") as f:
                        f.write(response.content)
                    return response_path
                else:
                    print(f"Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None

def main():
    # Initialize components
    recorder = AudioRecorder()
    camera = CameraCapture()
    api_client = VisionAPIClient()  # Update with your server URL if needed
    
    while True:
        print("\n1. Process Image and Voice Query")
        print("2. Exit")
        choice = input("Choose option (1-2): ")
        
        if choice == "1":
            # Capture image
            print("\nCapture image...")
            image_path = camera.capture_image()
            
            if image_path:
                # Record audio query
                print("\nPress Enter to start recording your question...")
                input()
                audio_path = recorder.record_audio("query.wav")
                
                # Send to API and get response
                print("\nProcessing with API...")
                response_file = api_client.process_image_and_query(image_path, audio_path)
                
                if response_file:
                    print("\nPlaying response...")
                    play_audio(response_file)
                else:
                    print("Failed to get response from server")
            else:
                print("Failed to capture image!")
                
        elif choice == "2":
            break
            
    print("Program ended")

if __name__ == "__main__":
    main()