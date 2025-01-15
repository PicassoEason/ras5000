import requests 
import pygame
import time
from urllib.parse import unquote
import json
import os
import RPi.GPIO as GPIO

class AudiobookPlayer:
    def __init__(self):
        # 設定GPIO
        self.BUTTON_PIN = 27  # 使用GPIO 27作為控制按鈕
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # 初始化pygame
        pygame.mixer.init()
        
        # 設定音頻目錄
        self.audio_dir = self.ensure_audio_directory()
        
        # 設定運行狀態
        self.is_running = True
        self.is_playing = False

    def ensure_audio_directory(self):
        """建立音頻目錄"""
        audio_dir = 'audio'
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
        return audio_dir

    def get_next_sentence(self):
        """獲取下一句音頻的URL"""
        api_url = "http://192.168.100.233:3100/next-sentence"
        api_url = f"{api_url}?book_id=Atomic habits ( PDFDrive ).pdf"
        
        try:
            response = requests.post(api_url)
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                print(f"API呼叫失敗: {response.status_code}")
                return None
        except Exception as e:
            print(f"發生錯誤: {e}")
            return None

    def download_and_play_audio(self, audio_url):
        """下載並播放音頻"""
        try:
            # 下載音頻檔案
            print("開始下載...")
            response = requests.get(audio_url, stream=True)
            if response.status_code == 200:
                # 解析檔案名稱
                filename = unquote(audio_url.split('/')[-1].split('?')[0])
                file_path = os.path.join(self.audio_dir, filename)
                
                # 儲存音頻檔案
                print(f"儲存檔案: {filename}")
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print("開始播放...")
                self.is_playing = True
                
                # 播放音頻
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                
                # 等待播放完成
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
                self.is_playing = False
                print("播放完成")
                
            else:
                print(f"下載音頻失敗: {response.status_code}")
                
        except Exception as e:
            print(f"播放時發生錯誤: {e}")
            self.is_playing = False

    def button_callback(self, channel):
        """按鈕回調函數"""
        time.sleep(0.1)  # 消除按鈕彈跳
        
        if GPIO.input(channel) == GPIO.LOW:  # 按鈕被按下
            if not self.is_playing:  # 只有在沒有播放時才處理按鈕事件
                print("按鈕被按下，播放下一句")
                audio_url = self.get_next_sentence()
                if audio_url:
                    print(f"收到音頻URL: {audio_url}")
                    self.download_and_play_audio(audio_url)

    def cleanup(self):
        """清理資源"""
        pygame.mixer.quit()
        GPIO.cleanup()

    def run(self):
        """主運行循環"""
        print("開始執行程式。按下按鈕播放下一句，按Ctrl+C退出")
        
        # 設置按鈕事件檢測
        GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, 
                            callback=self.button_callback, bouncetime=300)
        
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n程式結束")
            self.is_running = False
        finally:
            self.cleanup()

def main():
    player = AudiobookPlayer()
    player.run()

if __name__ == "__main__":
    main()