import requests 
import pygame
import time
from urllib.parse import unquote
import json
import os

def ensure_audio_directory():
    """
    Create 'audio' directory if it doesn't exist
    """
    audio_dir = 'audio'
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
    return audio_dir

def get_next_sentence():
    """
    Call API to get the URL of the next audio file
    """
    
    api_url = "http://192.168.100.160:3100/next-sentence"
    book_id = "1735953778384-Atomic habits ( PDFDrive ) shorter.pdf"
    api_url = f"{api_url}?book_id={book_id}"
    
    try:
        response = requests.post(api_url)
        if response.status_code == 200:
            # Parse JSON string and remove extra quotes
            return json.loads(response.text)
        else:
            print(f"API call failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def download_and_play_audio(audio_url):
    """
    Download and play audio file
    """
    try:
        # Ensure audio directory exists
        audio_dir = ensure_audio_directory()
        
        # Download audio file
        print("Starting download...")
        response = requests.get(audio_url, stream=True)
        if response.status_code == 200:
            # Parse filename from URL and create full path
            filename = unquote(audio_url.split('/')[-1].split('?')[0])
            file_path = os.path.join(audio_dir, filename)
            
            # Save audio file
            print(f"Saving file: {filename}")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print("Starting playback...")
            # Initialize pygame
            pygame.mixer.init()
            
            # Load and play audio file
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # Cleanup
            pygame.mixer.quit()
            print("Playback complete")
            
        else:
            print(f"Failed to download audio: {response.status_code}")
            
    except Exception as e:
        print(f"Error during playback: {e}")

def main():
    print("Program started. Press Enter to play next sentence, 'q' to quit")
    while True:
        audio_url = get_next_sentence()
        if audio_url:
            print(f"Received audio URL: {audio_url}")
            download_and_play_audio(audio_url)
        user_input = input("Press Enter for next sentence, 'q' to quit: ")
        if user_input.lower() == 'q':
            break

if __name__ == "__main__":
    main()