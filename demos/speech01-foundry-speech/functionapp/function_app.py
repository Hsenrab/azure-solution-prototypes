import json
import logging
import os
from urllib import error, request
from xml.sax.saxutils import escape

import azure.functions as func
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)


def synthesize_with_managed_identity(text: str) -> dict:
    speech_endpoint = os.environ["AZURE_AI_ENDPOINT"].rstrip("/")
    voice_name = os.getenv("AZURE_SPEECH_VOICE", "en-US-AvaMultilingualNeural")
    output_format = os.getenv("AZURE_SPEECH_OUTPUT_FORMAT", "riff-16khz-16bit-mono-pcm")
    access_token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    ssml = (
        "<speak version='1.0' xml:lang='en-US'>"
        f"<voice name='{voice_name}'>"
        f"{escape(text)}"
        "</voice>"
        "</speak>"
    )

    speech_request = request.Request(
        url=f"{speech_endpoint}/tts/cognitiveservices/v1",
        data=ssml.encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": output_format,
            "User-Agent": "speech01-managed-identity-demo",
        },
        method="POST",
    )

    try:
        with request.urlopen(speech_request, timeout=60) as speech_response:
            audio_bytes = speech_response.read()
            request_id = speech_response.headers.get("X-RequestId", "")
            content_type = speech_response.headers.get("Content-Type", "")
    except error.HTTPError as ex:
        error_body = ex.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Speech endpoint returned HTTP {ex.code}. Response body: {error_body}"
        ) from ex
    except error.URLError as ex:
        raise RuntimeError(f"Speech endpoint request failed: {ex}") from ex

    logging.info(
        "Managed identity Speech call succeeded. request_id=%s audio_bytes=%s voice=%s",
        request_id,
        len(audio_bytes),
        voice_name,
    )

    return {
        "input_text": text,
        "voice": voice_name,
        "speech_endpoint": speech_endpoint,
        "auth_mode": "managed_identity",
        "request_id": request_id,
        "content_type": content_type,
        "audio_bytes": len(audio_bytes),
        "message": "Managed identity successfully called the Speech endpoint.",
    }


@app.function_name(name="SpeechRoundtrip")
@app.route(route="speech-roundtrip", methods=["POST"])
def speech_roundtrip(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        body = {}

    text = (body.get("text") or "").strip()
    if not text:
        return func.HttpResponse(
            json.dumps({"error": "Request body must include a non-empty 'text' field."}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        result = synthesize_with_managed_identity(text)
    except Exception as ex:
        logging.exception("Managed identity Speech call failed")
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            status_code=500,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps(result, indent=2),
        status_code=200,
        mimetype="application/json",
    )
