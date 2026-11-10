
# Task: Integrate Gnani Prisma STT and Timbre TTS with audio conversion.

import io
import base64
import hashlib
import logging
import subprocess
import imageio_ffmpeg

from typing import Optional, Dict, Any, List
import httpx

from app.config import settings

logger = logging.getLogger("vyaparvoice.gnani")

# Credit preservation cache: md5(text + lang + voice) -> base64 audio
# Prevents wasting the competition's 5,000 credits on repeated phrases
_tts_cache: Dict[str, str] = {}


# Task: Convert browser-recorded audio into WAV format using FFmpeg.
def convert_audio_to_wav(audio_bytes: bytes) -> bytes:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    result = subprocess.run(
        [
            ffmpeg_exe,
            "-i", "pipe:0",
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            "pipe:1",
        ],
        input=audio_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    if not result.stdout:
        raise RuntimeError("FFmpeg produced empty audio output.")

    return result.stdout


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
        Maps short regional codes to Gnani BCP-47 language codes.
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
            "auto": "indic-auto",
        }

        return mapping.get(code, short_code)

    # Task: Transcribe converted WAV audio using Gnani Prisma STT.
    @staticmethod
    async def transcribe_audio(
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language_code: str = "indic-auto"
    ) -> Dict[str, Any]:

        api_key = GnaniService.get_api_key()
        gnani_lang = GnaniService.map_language_code(language_code)

        if not api_key:
            logger.warning(
                "GNANI_API_KEY not configured in backend/.env."
            )

            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma_unconfigured",
                "error": (
                    "GNANI_API_KEY is not set. Please add your Gnani API key "
                    "from https://app.gnani.ai to backend/.env."
                )
            }

        headers = {
            "X-API-Key-ID": api_key
        }

        # Task: Convert uploaded audio to WAV before calling Gnani.
        try:
            audio_bytes = convert_audio_to_wav(audio_bytes)
            filename = "voice_input.wav"

        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode(
                "utf-8",
                errors="ignore"
            )

            logger.error(
                f"FFmpeg audio conversion failed: {error_message}"
            )

            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma",
                "error": (
                    "Audio conversion failed. "
                    "Please try recording again."
                )
            }

        except Exception as e:
            logger.error(
                f"Audio conversion error: {str(e)}",
                exc_info=True
            )

            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma",
                "error": (
                    "Could not process the audio. "
                    "Please try recording again."
                )
            }

        # Task: Send converted WAV audio to Gnani Prisma.
        files = {
            "audio_file": (
                filename,
                audio_bytes,
                "audio/wav"
            )
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

                    # Detect language from Indic Unicode script blocks in transcript
                    script_lang = None
                    for char in transcript:
                        if '\u0B80' <= char <= '\u0BFF':
                            script_lang = "ta-IN"
                            break
                        if '\u0C80' <= char <= '\u0CFF':
                            script_lang = "kn-IN"
                            break
                        if '\u0D00' <= char <= '\u0D7F':
                            script_lang = "ml-IN"
                            break
                        if '\u0900' <= char <= '\u097F':
                            script_lang = "hi-IN"
                            break

                    detected = (
                        script_lang
                        or result.get("detected_language_code")
                        or result.get("detected_language")
                        or gnani_lang
                    )
   
                    confidence = float(
                        result.get("confidence", 0.95)
                    )

                    return {
                        "transcription": transcript.strip(),
                        "detected_language": detected,
                        "confidence": confidence,
                        "provider": "gnani_prisma",
                        "raw_response": result
                    }

                elif response.status_code == 401:
                    logger.error(
                        "Gnani Prisma 401 Unauthorized. Invalid API Key."
                    )

                    return {
                        "transcription": "",
                        "detected_language": gnani_lang,
                        "confidence": 0.0,
                        "provider": "gnani_prisma",
                        "error": (
                            "Gnani API Authentication Failed "
                            "(401 Unauthorized). Please check your key "
                            "at https://app.gnani.ai."
                        )
                    }

                elif response.status_code == 429:
                    logger.error(
                        "Gnani Prisma 429 Rate Limit Exceeded."
                    )

                    return {
                        "transcription": "",
                        "detected_language": gnani_lang,
                        "confidence": 0.0,
                        "provider": "gnani_prisma",
                        "error": (
                            "Gnani API credit limit reached "
                            "or rate limit exceeded."
                        )
                    }

                else:
                    logger.error(
                        f"Gnani Prisma returned HTTP "
                        f"{response.status_code}: {response.text}"
                    )

                    return {
                        "transcription": "",
                        "detected_language": gnani_lang,
                        "confidence": 0.0,
                        "provider": "gnani_prisma",
                        "error": (
                            f"Gnani STT API returned status "
                            f"{response.status_code}: {response.text}"
                        )
                    }

        except httpx.TimeoutException:
            logger.error(
                "Gnani Prisma request timed out after 30 seconds."
            )

            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma",
                "error": "Connection to Gnani Prisma STT timed out."
            }

        except Exception as e:
            logger.error(
                f"Error calling Gnani Prisma API: {str(e)}",
                exc_info=True
            )

            return {
                "transcription": "",
                "detected_language": gnani_lang,
                "confidence": 0.0,
                "provider": "gnani_prisma",
                "error": f"Gnani STT client exception: {str(e)}"
            }

    # Task: Synthesize speech using Gnani Timbre TTS.
    @staticmethod
    async def synthesize_speech(
        text: str,
        language: str = "en-IN",
        voice: str = "Shivani",
        speed: float = 1.0
    ) -> Optional[str]:

        if not text or not text.strip():
            return None

        clean_text = text.strip()
        gnani_lang = GnaniService.map_language_code(language)

        if gnani_lang == "indic-auto":
            gnani_lang = "en-IN"

        # Task: Check cache before spending Gnani credits.
        cache_key = hashlib.md5(
            f"{clean_text}:{gnani_lang}:{voice}:{speed}".encode("utf-8")
        ).hexdigest()

        if cache_key in _tts_cache:
            return _tts_cache[cache_key]

        api_key = GnaniService.get_api_key()

        if not api_key:
            logger.warning(
                "GNANI_API_KEY not configured. Skipping Timbre TTS call."
            )
            return None

        headers = {
            "X-API-Key-ID": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "text": clean_text,
            "model": settings.GNANI_TTS_MODEL or "timbre-v3.0",
            "voice": voice or "Shivani",
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
                    content_type = response.headers.get(
                        "content-type",
                        ""
                    )

                    audio_b64 = None

                    if (
                        "audio" in content_type
                        or "octet-stream" in content_type
                        or len(response.content) > 100
                    ):
                        audio_b64 = base64.b64encode(
                            response.content
                        ).decode("utf-8")

                    elif "json" in content_type:
                        data = response.json()

                        audio_b64 = (
                            data.get("audio")
                            or data.get("audio_base64")
                        )

                    if audio_b64:
                        _tts_cache[cache_key] = audio_b64
                        return audio_b64

                else:
                    logger.error(
                        f"Gnani Timbre returned status "
                        f"{response.status_code}: {response.text}"
                    )

        except Exception as e:
            logger.error(
                f"Error calling Gnani Timbre API: {str(e)}",
                exc_info=True
            )

        return None

    # Task: Verify Gnani API connectivity and credentials.
    @staticmethod
    async def verify_connectivity() -> Dict[str, Any]:

        api_key = GnaniService.get_api_key()

        if not api_key:
            return {
                "configured": False,
                "status": "missing_api_key",
                "message": (
                    "GNANI_API_KEY is not configured in backend/.env."
                ),
                "dashboard_url": "https://app.gnani.ai",
                "docs_url": (
                    "https://docs.gnani.ai/api/introduction/introduction"
                )
            }

        test_text = "Namaste"

        try:
            headers = {
                "X-API-Key-ID": api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "text": test_text,
                "model": settings.GNANI_TTS_MODEL or "timbre-v3.0",
                "voice": "Shivani",
                "language": "hi-IN",
                "speed": 1.0,
                "audio_config": {
                    "encoding": "linear_pcm",
                    "container": "wav",
                    "sample_rate": 16000
                }
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    settings.GNANI_TTS_ENDPOINT,
                    headers=headers,
                    json=payload
                )

                if res.status_code == 200:
                    return {
                        "configured": True,
                        "status": "active",
                        "message": (
                            "Gnani API key successfully verified "
                            "with https://api.vachana.ai."
                        ),
                        "models": {
                            "stt": settings.GNANI_STT_MODEL,
                            "tts": settings.GNANI_TTS_MODEL
                        }
                    }

                elif res.status_code == 401:
                    return {
                        "configured": True,
                        "status": "unauthorized",
                        "message": (
                            "Gnani API key rejected (401 Unauthorized). "
                            "Please check your key at https://app.gnani.ai."
                        )
                    }

                else:
                    return {
                        "configured": True,
                        "status": "error",
                        "message": (
                            f"Gnani API returned status "
                            f"{res.status_code}: {res.text}"
                        )
                    }

        except Exception as e:
            return {
                "configured": True,
                "status": "unreachable",
                "message": (
                    f"Could not reach Gnani API endpoint: {str(e)}"
                )
            }
