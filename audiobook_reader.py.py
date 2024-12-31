import requests 
import pygame
import time
from urllib.parse import unquote
import json

def get_next_sentence():
    """
    呼叫API取得下一句的音檔網址
    """
    api_url = "http://192.168.100.233:3100/next-sentence"
    api_url = f"{api_url}?book_id=Atomic habits ( PDFDrive ).pdf"
    
    try:
        response = requests.post(api_url)
        if response.status_code == 200:
            # 解析回傳的 JSON 字串，移除多餘的引號
            return json.loads(response.text)
        else:
            print(f"API呼叫失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None

def download_and_play_audio(audio_url):
    """
    下載並播放音檔
    """
    try:
        # 下載音檔
        print("開始下載音檔...")
        response = requests.get(audio_url, stream=True)
        if response.status_code == 200:
            # 從 URL 中解析檔名
            filename = unquote(audio_url.split('/')[-1].split('?')[0])
            
            # 儲存音檔
            print(f"儲存音檔: {filename}")
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print("開始播放音檔...")
            # 初始化pygame
            pygame.mixer.init()
            
            # 載入並播放音檔
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # 清理
            pygame.mixer.quit()
            print("播放完成")
            
        else:
            print(f"下載音檔失敗: {response.status_code}")
            
    except Exception as e:
        print(f"播放音檔時發生錯誤: {e}")

def main():
    print("程式啟動，按 Enter 播放下一句，輸入 q 退出")
    while True:
        audio_url = get_next_sentence()
        if audio_url:
            print(f"取得的音檔 URL: {audio_url}")
            download_and_play_audio(audio_url)
        user_input = input("按Enter繼續播放下一句，輸入q退出: ")
        if user_input.lower() == 'q':
            break

if __name__ == "__main__":
    main()