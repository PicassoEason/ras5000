import os
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import time
from datetime import datetime
import subprocess

class VisionTextReader:
    def __init__(self):
        # Vision API credentials
        self.vision_key = "9LmIPsS2ba2Z85lW3aTpJZKgjpCoEYbkKYSCRhyQwjQmuhDZG0bGJQQJ99ALACYeBjFXJ3w3AAAFACOGuJxl"
        self.vision_endpoint = "https://visionxstudio.cognitiveservices.azure.com/"
        
        # Speech API credentials
        self.speech_key = '8QDp6O6wIPVAzyXs5KqMILclqqZqxefgBkT4vxiRzNmFr2OcXHbBJQQJ99ALACYeBjFXJ3w3AAAYACOGv8QR'
        self.speech_region = 'eastus'
        
        # Initialize clients
        self.init_vision_client()
        self.init_speech_config()
        
        # Ensure image directory exists
        self.image_dir = 'image/temp'
        os.makedirs(self.image_dir, exist_ok=True)

    def init_vision_client(self):
        """Initialize Computer Vision client"""
        self.vision_client = ComputerVisionClient(
            self.vision_endpoint, 
            CognitiveServicesCredentials(self.vision_key)
        )

    def init_speech_config(self):
        """Initialize Speech configuration"""
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.speech_region
        )
        self.speech_config.speech_synthesis_voice_name = 'en-US-JennyMultilingualNeural'
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, 
            audio_config=speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        )

    def capture_image(self):
        """Capture image using libcamera-still"""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.image_dir, f'capture_{timestamp}.jpg')
            
            # Use libcamera-still to capture image
            print("Press Enter to capture an image...")
            input()  # Wait for user input
            
            # Capture image using libcamera-still
            command = [
                'libcamera-still',
                '-o', filename,
                '--width', '1920',
                '--height', '1080',
                '--immediate'  # Take picture immediately
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

    def read_image(self, image_path):
        """Read text from image and return results"""
        print(f"Reading text from image: {image_path}")
        
        with open(image_path, "rb") as image_stream:
            read_response = self.vision_client.read_in_stream(image_stream, raw=True)
            
        # Get operation ID
        operation_location = read_response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]

        # Wait for the operation to complete
        while True:
            read_result = self.vision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)

        # Process and return results
        extracted_texts = []
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    extracted_texts.append(line.text)

        return extracted_texts

    def speak_text(self, text):
        """Synthesize text to speech"""
        print(f"Speaking: {text}")
        result = self.speech_synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.Canceled:
            print(f"Speech synthesis canceled: {result.cancellation_details.reason}")

def main():
    # Initialize the reader
    reader = VisionTextReader()
    
    while True:
        # Capture image from camera
        print("\nOpening camera...")
        image_path = reader.capture_image()
        
        if image_path is None:
            print("No image captured. Exiting...")
            break
            
        # Extract text from image
        print("\nStarting text extraction...")
        extracted_texts = reader.read_image(image_path)
        
        if not extracted_texts:
            print("No text detected in the image.")
            continue
            
        # Read each line of text
        print("\nStarting text-to-speech...")
        for text in extracted_texts:
            reader.speak_text(text)
            time.sleep(0.5)  # Small pause between lines
            
        # Ask if user wants to capture another image
        user_input = input("\nPress Enter to capture another image, or 'q' to quit: ")
        if user_input.lower() == 'q':
            break

if __name__ == "__main__":
    main()