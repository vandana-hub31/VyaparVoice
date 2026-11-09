import io
import base64
import hashlib
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.config import settings

logger = logging.getLogger("vyaparvoice.gnani")

# Credit preservation cache: md5(text + lang + voice) -> base64 audio
# Prevents wasting the competition's 5,000 credits on repeated phrases
_tts_cache: Dict[str, str] = {}

class GnaniService:
    """
    Official Gnani.ai Speech Services Integration
    Documentation: https://docs.gnani.ai/api/introduction/introduction
    Base URL: https://api.vachana.ai
    Auth: X-API-Key-ID header
    """

    @staticmethod
    def get_api_key() -> Optional[str]:
        key = settings.GNANI_API_KEY.strip() if settings.GNANI_API_KEY else ""
        return key if len(key) > 0 else None

    @staticmethod
    def map_language_code(short_code: str) -> str:
        """
        Maps short regional codes to Gnani BCP-47 language codes
        Supported by Prisma & Timbre: kn-IN, ml-IN, hi-IN, en-IN, etc.
        """
        code = short_code.lower().strip()
        mapping = {
            "kn": "kn-IN",
            "kannada": "kn-IN",
            "ml": "ml-IN",
            "malayalam": "ml-IN",
            "hi": "hi-IN",
            "hindi": "hi-IN",
            "en": "en-IN",
            "english": "en-IN",
            "ta": "ta-IN",
            "tamil": "ta-IN",
            "auto": "indic-auto"
        }
        return mapping.get(code, short_code)

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
        Parameters:
            - audio_file: multipart binary file (WAV)
            - model: prisma-v3.0
            - language_code: indic-auto (or kn-IN, ml-IN, hi-IN, en-IN)
            - format: transcribe
        """
        api_key = GnaniService.get_api_key()
        gnani_lang = GnaniService.map_language_code(language_code)

        if not api_key:
            logger.warning("GNANI_API_KEY not configured in backend/.env. Returning status for user setup.")
            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma_unconfigured",
                "error": "GNANI_API_KEY is not set. Please add your Gnani API key from https://app.gnani.ai to backend/.env."
            }

        headers = {
            "X-API-Key-ID": api_key
        }
        files = {
            "audio_file": (filename, audio_bytes, "audio/wav")
        }
        data = {
            "model": settings.GNANI_STT_MODEL or "prisma-v3.0",
            "language_code": gnani_lang,
            "format": "transcribe"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.GNANI_STT_ENDPOINT,
                    headers=headers,
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    result = response.json()
                    transcript = (
                        result.get("transcription")
                        or result.get("text")
                        or result.get("transcript")
                        or ""
                    )
                    detected = result.get("detected_language") or gnani_lang
                    confidence = float(result.get("confidence", 0.95))

                    return {
                        "transcription": transcript.strip(),
                        "detected_language": detected,
                        "confidence": confidence,
                        "provider": "gnani_prisma",
                        "raw_response": result
                    }
                elif response.status_code == 401:
                    logger.error("Gnani Prisma 401 Unauthorized. Invalid API Key.")
                    return {
                        "transcription": "",
                        "detected_language": gnani_lang,
                        "confidence": 0.0,
                        "provider": "gnani_prisma",
                        "error": "Gnani API Authentication Failed (401 Unauthorized). Please check your key at https://app.gnani.ai."
                    }
                elif response.status_code == 429:
                    logger.error("Gnani Prisma 429 Rate Limit Exceeded.")
                    return {
                        "transcription": "",
                        "detected_language": gnani_lang,
                        "confidence": 0.0,
                        "provider": "gnani_prisma",
                        "error": "Gnani API credit limit reached or rate limit exceeded."
                    }
                else:
                    logger.error(f"Gnani Prisma returned HTTP {response.status_code}: {response.text}")
                    return {
                        "transcription": "",
                        "detected_language": gnani_lang,
                        "confidence": 0.0,
                        "provider": "gnani_prisma",
                        "error": f"Gnani STT API returned status {response.status_code}: {response.text}"
                    }

        except httpx.TimeoutException:
            logger.error("Gnani Prisma request timed out after 30 seconds.")
            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma",
                "error": "Connection to Gnani Prisma STT timed out."
            }
        except Exception as e:
            logger.error(f"Error calling Gnani Prisma API: {str(e)}", exc_info=True)
            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma",
                "error": f"Gnani STT client exception: {str(e)}"
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
        Body:
            {
              "text": "...",
              "model": "timbre-v3.0",
              "voice": "Nalini",
              "language": "kn-IN",
              "speed": 1.0,
              "audio_config": {
                "encoding": "linear_pcm",
                "container": "wav",
                "sample_rate": 22050
              }
            }
        Returns Base64 encoded WAV audio string.
        """
        if not text or not text.strip():
            return None

        clean_text = text.strip()
        gnani_lang = GnaniService.map_language_code(language)
        if gnani_lang == "indic-auto":
            gnani_lang = "en-IN"

        # Check Credit Preservation Cache first
        cache_key = hashlib.md5(f"{clean_text}:{gnani_lang}:{voice}:{speed}".encode("utf-8")).hexdigest()
        if cache_key in _tts_cache:
            return _tts_cache[cache_key]

        api_key = GnaniService.get_api_key()
        if not api_key:
            logger.warning("GNANI_API_KEY not configured. Skipping Timbre TTS call.")
            return None

        headers = {
            "X-API-Key-ID": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": clean_text,
            "model": settings.GNANI_TTS_MODEL or "timbre-v3.0",
            "voice": voice or "Nalini",
            "language": gnani_lang,
            "speed": speed,
            "audio_config": {
                "encoding": "linear_pcm",
                "container": "wav",
                "num_channels": 1,
                "sample_rate": 22050
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.GNANI_TTS_ENDPOINT,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    audio_b64 = None

                    # If response is raw binary audio (standard per docs.gnani.ai)
                    if "audio" in content_type or "octet-stream" in content_type or len(response.content) > 100:
                        audio_b64 = base64.b64encode(response.content).decode("utf-8")
                    elif "json" in content_type:
                        data = response.json()
                        audio_b64 = data.get("audio") or data.get("audio_base64")

                    if audio_b64:
                        # Save in credit preservation cache
                        _tts_cache[cache_key] = audio_b64
                        return audio_b64
                else:
                    logger.error(f"Gnani Timbre returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error calling Gnani Timbre API: {str(e)}", exc_info=True)

        return None

    @staticmethod
    async def verify_connectivity() -> Dict[str, Any]:
        """
        Diagnose Gnani API key and service reachability.
        """
        api_key = GnaniService.get_api_key()
        if not api_key:
            return {
                "configured": False,
                "status": "missing_api_key",
                "message": "GNANI_API_KEY is not configured in backend/.env.",
                "dashboard_url": "https://app.gnani.ai",
                "docs_url": "https://docs.gnani.ai/api/introduction/introduction"
            }

        # Test small synthesis to check credentials
        test_text = "Namaste"
        try:
            headers = {
                "X-API-Key-ID": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": test_text,
                "model": settings.GNANI_TTS_MODEL or "timbre-v3.0",
                "voice": "Nalini",
                "language": "hi-IN",
                "speed": 1.0,
                "audio_config": {
                    "encoding": "linear_pcm",
                    "container": "wav",
                    "sample_rate": 16000
                }
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(settings.GNANI_TTS_ENDPOINT, headers=headers, json=payload)
                if res.status_code == 200:
                    return {
                        "configured": True,
                        "status": "active",
                        "message": "Gnani API key successfully verified with https://api.vachana.ai.",
                        "models": {
                            "stt": settings.GNANI_STT_MODEL,
                            "tts": settings.GNANI_TTS_MODEL
                        }
                    }
                elif res.status_code == 401:
                    return {
                        "configured": True,
                        "status": "unauthorized",
                        "message": "Gnani API key rejected (401 Unauthorized). Please check your key at https://app.gnani.ai."
                    }
                else:
                    return {
                        "configured": True,
                        "status": "error",
                        "message": f"Gnani API returned status {res.status_code}: {res.text}"
                    }
        except Exception as e:
            return {
                "configured": True,
                "status": "unreachable",
                "message": f"Could not reach Gnani API endpoint: {str(e)}"
            }
