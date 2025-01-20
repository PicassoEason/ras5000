import os
import pyaudio
import wave
import pygame
import requests
import json
import time
import subprocess
from datetime import datetime
from urllib.parse import unquote

class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5
        
        # Ensure directories exist
        self.temp_dir = "temp_files"
        self.audio_dir = "audio"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
    def record_audio(self, output_filename):
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
        self.image_dir = 'image/temp'
        os.makedirs(self.image_dir, exist_ok=True)
        
    def capture_image(self):
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

class APIClient:
    def __init__(self, base_url="http://192.168.100.160:3100"):
        self.base_url = base_url
        
    def get_next_sentence(self, book_id="1735953778384-Atomic habits ( PDFDrive ) shorter.pdf"):
        api_url = f"{self.base_url}/next-sentence?book_id={book_id}"
        try:
            response = requests.post(api_url)
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                print(f"API call failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error occurred: {e}")
            return None
    
    def send_voice_query(self, audio_file):
        url = f"{self.base_url}/rag-voice-assistant"
        
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return None
            
        files = {'file': ('query.wav', open(audio_file, 'rb'), 'audio/wav')}
        
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
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
        url = f"{self.base_url}/process-ocr-image-and-audio"
        
        if not os.path.exists(image_file) or not os.path.exists(audio_file):
            print("Image or audio file not found")
            return None
            
        files = {
            'image': ('image.jpg', open(image_file, 'rb'), 'image/jpeg'),
            'audio': ('query.wav', open(audio_file, 'rb'), 'audio/wav')
        }
        
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
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
                
    def process_vision_query(self, image_file, audio_file):
        url = f"{self.base_url}/process-text-and-image"
        
        if not os.path.exists(image_file) or not os.path.exists(audio_file):
            print("Image or audio file not found")
            return None
            
        files = {
            'image': ('image.jpg', open(image_file, 'rb'), 'image/jpeg'),
            'audio': ('query.wav', open(audio_file, 'rb'), 'audio/wav')
        }
        
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                response_path = os.path.join('temp_files', "vision_response.wav")
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

class AudioPlayer:
    @staticmethod
    def play_audio(filename):
        if not os.path.exists(filename):
            print(f"Audio file not found: {filename}")
            return
            
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()

    @staticmethod
    def download_and_play_audio(audio_url):
        try:
            audio_dir = "audio"
            os.makedirs(audio_dir, exist_ok=True)
            
            print("Starting download...")
            response = requests.get(audio_url, stream=True)
            if response.status_code == 200:
                filename = unquote(audio_url.split('/')[-1].split('?')[0])
                file_path = os.path.join(audio_dir, filename)
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print("Starting playback...")
                AudioPlayer.play_audio(file_path)
                print("Playback complete")
            else:
                print(f"Failed to download audio: {response.status_code}")
                
        except Exception as e:
            print(f"Error during playback: {e}")

def main():
    recorder = AudioRecorder()
    camera = CameraCapture()
    api_client = APIClient()
    audio_player = AudioPlayer()
    
    while True:
        print("\n=== Unified Client Application ===")
        print("1. Audiobook Player")
        print("2. Voice Query Assistant")
        print("3. OCR + Voice Query")
        print("4. Vision + Voice Query")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ")
        
        if choice == "1":
            print("\n=== Audiobook Player Mode ===")
            while True:
                audio_url = api_client.get_next_sentence()
                if audio_url:
                    print(f"Received audio URL: {audio_url}")
                    audio_player.download_and_play_audio(audio_url)
                user_input = input("Press Enter for next sentence, 'b' to go back to main menu: ")
                if user_input.lower() == 'b':
                    break
                    
        elif choice == "2":
            print("\n=== Voice Query Mode ===")
            print("Press Enter to start recording...")
            input()
            audio_path = recorder.record_audio("query.wav")
            
            print("Sending request to server...")
            response_file = api_client.send_voice_query(audio_path)
            
            if response_file:
                print("Playing response...")
                audio_player.play_audio(response_file)
                
        elif choice == "3":
            print("\n=== OCR + Voice Query Mode ===")
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
                    audio_player.play_audio(response_file)
                    
        elif choice == "4":
            print("\n=== Vision + Voice Query Mode ===")
            print("Taking photo...")
            image_path = camera.capture_image()
            
            if image_path:
                print("Press Enter to start recording...")
                input()
                audio_path = recorder.record_audio("query.wav")
                
                print("Sending request to server...")
                response_file = api_client.process_vision_query(image_path, audio_path)
                
                if response_file:
                    print("Playing response...")
                    audio_player.play_audio(response_file)
                    
        elif choice == "5":
            print("\nThank you for using the Unified Client Application!")
            break
            
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()