import os
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI

# This example requires environment variables named "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT" and "AZURE_OPENAI_CHAT_DEPLOYMENT"
# Your endpoint should look like the following https://YOUR_OPEN_AI_RESOURCE_NAME.openai.azure.com/
client = AzureOpenAI(
azure_endpoint="https://openai-imagine-cup-2.openai.azure.com/",
api_key="CbaOkOgaVrPrsvAP5FlTCMJ2wisP08098HWqVCANL15pJtOpAllxJQQJ99ALACHYHv6XJ3w3AAABACOGSu9m",
api_version="2023-05-15"
)

# This will correspond to the custom name you chose for your deployment when you deployed a model.
deployment_id="gpt-4o"

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
speech_config = speechsdk.SpeechConfig(subscription='8QDp6O6wIPVAzyXs5KqMILclqqZqxefgBkT4vxiRzNmFr2OcXHbBJQQJ99ALACYeBjFXJ3w3AAAYACOGv8QR', region='eastus')
audio_output_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Should be the locale for the speaker's language.
speech_config.speech_recognition_language="en-US"
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# The language of the voice that responds on behalf of Azure OpenAI.
speech_config.speech_synthesis_voice_name='en-US-JennyMultilingualNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)
# tts sentence end mark
tts_sentence_end = [ ".", "!", "?", ";", "。", "！", "？", "；", "\n" ]

# Prompts Azure OpenAI with a request and synthesizes the response.
def ask_azure_openai(prompt):
    # Ask Azure OpenAI in streaming way
    response = client.chat.completions.create(model=deployment_id, max_tokens=200, stream=True, messages=[
        {"role": "user", "content": prompt}
    ])
    collected_messages = []
    last_tts_request = None

    # iterate through the stream response stream
    for chunk in response:
        if len(chunk.choices) > 0:
            chunk_message = chunk.choices[0].delta.content  # extract the message
            if chunk_message is not None:
                collected_messages.append(chunk_message)  # save the message
                if chunk_message in tts_sentence_end: # sentence end found
                    text = ''.join(collected_messages).strip() # join the recieved message together to build a sentence
                    if text != '': # if sentence only have \n or space, we could skip
                        print(f"Speech synthesized to speaker for: {text}")
                        last_tts_request = speech_synthesizer.speak_text_async(text)
                        collected_messages.clear()
    if last_tts_request:
        last_tts_request.get()

# Continuously listens for speech input to recognize and send as text to Azure OpenAI
def chat_with_azure_openai():
    while True:
        print("Azure OpenAI is listening. Say 'Stop' or press Ctrl-Z to end the conversation.")
        try:
            # Get audio from the microphone and then send it to the TTS service.
            speech_recognition_result = speech_recognizer.recognize_once_async().get()

            # If speech is recognized, send it to Azure OpenAI and listen for the response.
            if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                if speech_recognition_result.text == "Stop.": 
                    print("Conversation ended.")
                    break
                print("Recognized speech: {}".format(speech_recognition_result.text))
                ask_azure_openai(speech_recognition_result.text)
            elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
                print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
                break
            elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_recognition_result.cancellation_details
                print("Speech Recognition canceled: {}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print("Error details: {}".format(cancellation_details.error_details))
        except EOFError:
            break

# Main

try:
    chat_with_azure_openai()
except Exception as err:
    print("Encountered exception. {}".format(err))