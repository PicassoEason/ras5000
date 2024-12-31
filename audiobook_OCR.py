import os
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import time

class VisionTextReader:
    def __init__(self):
        # Vision API credentials
        self.vision_key = "9LmIPsS2ba2Z85lW3aTpJZKgjpCoEYbkKYSCRhyQwjQmuhDZG0bGJQQJ99AKACYeBjFXJ3w3AAAFACOGuJxl"
        self.vision_endpoint = "https://visionxstudio.cognitiveservices.azure.com/"
        
        # Speech API credentials
        self.speech_key = '8QDp6O6wIPVAzyXs5KqMILclqqZqxefgBkT4vxiRzNmFr2OcXHbBJQQJ99ALACYeBjFXJ3w3AAAYACOGv8QR'
        self.speech_region = 'eastus'
        
        # Initialize clients
        self.init_vision_client()
        self.init_speech_config()

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
    
    # Specify image path
    image_path = r"C:\Users\Eason\Desktop\Rasberrypi-MVP\image\book.png"
    
    # Extract text from image
    print("Starting text extraction...")
    extracted_texts = reader.read_image(image_path)
    
    # Read each line of text
    print("\nStarting text-to-speech...")
    for text in extracted_texts:
        reader.speak_text(text)
        time.sleep(0.5)  # Small pause between lines

if __name__ == "__main__":
    main()