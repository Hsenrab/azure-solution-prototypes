import json
import os
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


def run_roundtrip(text: str, output_dir: Path) -> dict:
    if os.getenv("AZURE_AUTH_MODE", "").lower() != "aad":
        raise RuntimeError("This script supports managed identity / AAD mode only.")

    speech_endpoint = os.environ["AZURE_AI_ENDPOINT"]
    voice_name = os.getenv("AZURE_SPEECH_VOICE", "en-US-AvaMultilingualNeural")

    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    speech_config = speechsdk.SpeechConfig(endpoint=speech_endpoint)
    speech_config.authorization_token = token
    speech_config.speech_synthesis_voice_name = voice_name
    speech_config.speech_recognition_language = "en-US"

    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "speech01-roundtrip.wav"
    json_path = output_dir / "speech01-roundtrip.json"

    audio_output = speechsdk.audio.AudioOutputConfig(filename=str(wav_path))
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
    synth_result = synthesizer.speak_text_async(text).get()
    if synth_result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = speechsdk.SpeechSynthesisCancellationDetails.from_result(synth_result)
        raise RuntimeError(f"Speech synthesis failed: {details.reason} | {details.error_details}")

    audio_input = speechsdk.audio.AudioConfig(filename=str(wav_path))
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    recog_result = recognizer.recognize_once_async().get()

    recognized_text = ""
    if recog_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        recognized_text = recog_result.text

    result = {
        "input_text": text,
        "voice": voice_name,
        "wav_path": str(wav_path),
        "recognized_text": recognized_text,
        "recognition_reason": str(recog_result.reason),
    }
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    load_dotenv(dotenv_path="../env/.env")
    output = run_roundtrip(
        text="This is a Foundry aligned Azure Speech roundtrip test.",
        output_dir=Path("../outputs"),
    )
    print(json.dumps(output, indent=2))
