import requests
import pyaudio
import wave
import pygame
import cv2
import numpy as np
from PIL import Image
import io
import time

class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5  # 可以調整錄音時間
        
    def record_audio(self, output_filename):
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
        
        wf = wave.open(output_filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

class CameraCapture:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)  # 使用樹梅派的攝像頭
        
    def capture_image(self, output_filename):
        ret, frame = self.camera.read()
        if ret:
            cv2.imwrite(output_filename, frame)
            return True
        return False
    
    def release(self):
        self.camera.release()

def play_audio(filename):
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

class APIClient:
    def __init__(self, base_url="http://your-server-url:8000"):
        self.base_url = base_url
        
    def send_voice_query(self, audio_file):
        """發送語音查詢到 RAG Voice Assistant API"""
        url = f"{self.base_url}/rag-voice-assistant"
        files = {'file': ('query.wav', open(audio_file, 'rb'), 'audio/wav')}
        
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                # 儲存回應的音訊
                with open("response.wav", "wb") as f:
                    f.write(response.content)
                return "response.wav"
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None

    def send_ocr_query(self, image_file, audio_file):
        """發送圖片和語音到 OCR Image and Audio API"""
        url = f"{self.base_url}/process-ocr-image-and-audio"
        files = {
            'image': ('image.jpg', open(image_file, 'rb'), 'image/jpeg'),
            'audio': ('query.wav', open(audio_file, 'rb'), 'audio/wav')
        }
        
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                # 儲存回應的音訊
                with open("ocr_response.wav", "wb") as f:
                    f.write(response.content)
                return "ocr_response.wav"
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None

def main():
    # 初始化所需的類別
    recorder = AudioRecorder()
    camera = CameraCapture()
    api_client = APIClient()  # 記得更改成你的伺服器 URL
    
    while True:
        print("\n1. Voice Query")
        print("2. OCR + Voice Query")
        print("3. Exit")
        choice = input("選擇功能 (1-3): ")
        
        if choice == "1":
            # 語音查詢
            print("按 Enter 開始錄音...")
            input()
            recorder.record_audio("query.wav")
            
            print("發送請求到伺服器...")
            response_file = api_client.send_voice_query("query.wav")
            
            if response_file:
                print("播放回應...")
                play_audio(response_file)
                
        elif choice == "2":
            # OCR + 語音查詢
            print("拍照中...")
            camera.capture_image("image.jpg")
            
            print("按 Enter 開始錄音...")
            input()
            recorder.record_audio("query.wav")
            
            print("發送請求到伺服器...")
            response_file = api_client.send_ocr_query("image.jpg", "query.wav")
            
            if response_file:
                print("播放回應...")
                play_audio(response_file)
                
        elif choice == "3":
            break
            
    camera.release()
    print("程式結束")

if __name__ == "__main__":
    main()