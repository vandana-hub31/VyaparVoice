import io
import base64
import logging
from typing import Optional, Dict, Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class GnaniService:
    @staticmethod
    async def transcribe_audio(
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language_code: str = "indic-auto"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Gnani Prisma STT (v3.0).
        Endpoint: POST https://api.vachana.ai/stt/v3
        Header: X-API-Key-ID: <GNANI_API_KEY>
        """
        api_key = settings.GNANI_API_KEY.strip() if settings.GNANI_API_KEY else None
        
        if api_key:
            try:
                headers = {
                    "X-API-Key-ID": api_key
                }
                files = {
                    "audio_file": (filename, audio_bytes, "audio/wav")
                }
                data = {
                    "model": settings.GNANI_STT_MODEL,
                    "language_code": language_code,
                    "format": "transcribe"
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        settings.GNANI_STT_ENDPOINT,
                        headers=headers,
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        result = response.json()
                        text = result.get("transcription") or result.get("text") or ""
                        lang = result.get("detected_language") or language_code
                        confidence = float(result.get("confidence", 0.95))
                        return {
                            "transcription": text,
                            "detected_language": lang,
                            "confidence": confidence,
                            "provider": "gnani_prisma"
                        }
                    else:
                        logger.warning(f"Gnani Prisma returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error calling Gnani Prisma API: {str(e)}")

        # Fallback / Demo Mode handler
        # If API key is not configured or remote API fails, return clean status
        return {
            "transcription": "",
            "detected_language": language_code if language_code != "indic-auto" else "en-IN",
            "confidence": 0.0,
            "provider": "offline_fallback",
            "note": "Gnani API key not configured or endpoint unreachable. Set GNANI_API_KEY in .env."
        }

    @staticmethod
    async def synthesize_speech(
        text: str,
        language: str = "en-IN",
        voice: str = "Nalini",
        speed: float = 1.0
    ) -> Optional[str]:
        """
        Synthesize speech using Gnani Timbre TTS (v3.0).
        Endpoint: POST https://api.vachana.ai/api/v1/tts/inference
        Header: X-API-Key-ID: <GNANI_API_KEY>
        Returns base64 encoded audio.
        """
        api_key = settings.GNANI_API_KEY.strip() if settings.GNANI_API_KEY else None

        # Map short language codes to Gnani locales if needed
        lang_map = {
            "en": "en-IN",
            "hi": "hi-IN",
            "kn": "kn-IN",
            "ml": "ml-IN"
        }
        gnani_lang = lang_map.get(language, language)

        if api_key:
            try:
                headers = {
                    "X-API-Key-ID": api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "model": settings.GNANI_TTS_MODEL,
                    "voice": voice,
                    "language": gnani_lang,
                    "speed": speed
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        settings.GNANI_TTS_ENDPOINT,
                        headers=headers,
                        json=payload
                    )
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "json" in content_type:
                            data = response.json()
                            audio_b64 = data.get("audio") or data.get("audio_base64")
                            return audio_b64
                        else:
                            # Direct binary audio response
                            return base64.b64encode(response.content).decode("utf-8")
                    else:
                        logger.warning(f"Gnani Timbre returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error calling Gnani Timbre API: {str(e)}")

        return None
