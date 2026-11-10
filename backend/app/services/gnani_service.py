
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
    if not audio_bytes or len(audio_bytes) < 100:
        raise ValueError("Audio recording is empty or too short. Please speak clearly into the microphone.")

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # Write to a temporary file so FFmpeg can seek container formats (e.g. mp4, m4a, webm, ogg)
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as in_file:
        in_file.write(audio_bytes)
        in_path = in_file.name

    out_path = in_path + ".wav"

    try:
        result = subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                "-i", in_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-f", "wav",
                out_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        with open(out_path, "rb") as f:
            wav_bytes = f.read()

        if not wav_bytes or len(wav_bytes) < 1000:
            raise ValueError("Audio recording is too brief to contain clear speech.")

        # Check silence: inspect 16-bit PCM samples after the 44-byte WAV header
        if len(wav_bytes) > 44:
            pcm_data = wav_bytes[44:]
            chunk = pcm_data[:32000]
            if chunk:
                max_val = max(abs(int.from_bytes(chunk[i:i+2], byteorder="little", signed=True)) for i in range(0, len(chunk)-1, 2))
                if max_val < 50:
                    raise ValueError("Audio recording contains no audible speech. Please speak into the microphone.")

        return wav_bytes
    finally:
        for p in [in_path, out_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


class GnaniService:
    """
    Official Gnani.ai Speech Services Integration
    Documentation: https://docs.gnani.ai/api/introduction/introduction
    Base URL: https://api.vachana.ai
    Auth: X-API-Key-ID header
    """

    SUPPORTED_TIMBRE_VOICES = {
        "Shivani", "Avinash", "Lakshmi", "Kalpana", "Shubham", "Prakash",
        "Devansh", "Yashraj", "Chetana", "Vasudha", "Harshad", "Riyaa", "Tarika"
    }

    @staticmethod
    def get_api_key() -> Optional[str]:
        key = settings.GNANI_API_KEY.strip() if settings.GNANI_API_KEY else ""
        return key if len(key) > 0 else None

    @staticmethod
    def map_language_code(short_code: Optional[str]) -> str:
        """
        Maps short regional codes to Gnani BCP-47 language codes.
        """
        if not short_code:
            return "indic-auto"
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
            "indic-auto": "indic-auto",
            "autodetect": "indic-auto",
            "auto-detect": "indic-auto",
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
                "detected_language": gnani_lang if gnani_lang != "indic-auto" else "en-IN",
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

        except ValueError as e:
            return {
                "transcription": "",
                "detected_language": gnani_lang if gnani_lang != "indic-auto" else "en-IN",
                "confidence": 0.0,
                "provider": "gnani_prisma",
                "error": str(e)
            }

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
                "detected_language": gnani_lang if gnani_lang != "indic-auto" else "en-IN",
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
                "detected_language": gnani_lang if gnani_lang != "indic-auto" else "en-IN",
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
                        result.get("transcript")
                        or result.get("transcription")
                        or result.get("text")
                        or (result.get("results") and isinstance(result["results"], list) and len(result["results"]) > 0 and result["results"][0].get("transcript"))
                        or (result.get("data") and isinstance(result["data"], dict) and (result["data"].get("transcript") or result["data"].get("transcription") or result["data"].get("text")))
                        or result.get("asr_output")
                        or ""
                    )

                    if isinstance(transcript, list):
                        transcript = " ".join(str(t) for t in transcript)
                    transcript = str(transcript).strip()

                    # 1. Prefer language detected by Gnani when valid
                    gnani_detected = (
                        result.get("detected_language_code")
                        or result.get("detected_language")
                        or (result.get("data") and isinstance(result["data"], dict) and (result["data"].get("detected_language_code") or result["data"].get("detected_language")))
                    )

                    valid_gnani_lang = None
                    if gnani_detected and isinstance(gnani_detected, str):
                        clean_detected = gnani_detected.strip().lower()
                        if clean_detected not in ["auto", "indic-auto", "unknown", "none", ""]:
                            valid_gnani_lang = GnaniService.map_language_code(clean_detected)

                    # 2. Script-based fallback detection
                    script_lang = None
                    for char in transcript:
                        if '\u0C80' <= char <= '\u0CFF': # Kannada
                            script_lang = "kn-IN"
                            break
                        elif '\u0D00' <= char <= '\u0D7F': # Malayalam
                            script_lang = "ml-IN"
                            break
                        elif '\u0900' <= char <= '\u097F': # Devanagari (Hindi)
                            script_lang = "hi-IN"
                            break
                        elif '\u0B80' <= char <= '\u0BFF': # Tamil
                            script_lang = "ta-IN"
                            break

                    if valid_gnani_lang and valid_gnani_lang not in ["auto", "indic-auto"]:
                        detected = valid_gnani_lang
                    elif script_lang:
                        detected = script_lang
                    else:
                        detected = gnani_lang if gnani_lang not in ["auto", "indic-auto"] else "en-IN"

                    confidence = float(
                        result.get("confidence", 0.95)
                    )

                    return {
                        "transcription": transcript,
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

        # Task: Ensure requested voice is supported, otherwise fallback safely to Shivani
        selected_voice = voice if voice in GnaniService.SUPPORTED_TIMBRE_VOICES else "Shivani"

        # Task: Check cache before spending Gnani credits.
        cache_key = hashlib.md5(
            f"{clean_text}:{gnani_lang}:{selected_voice}:{speed}".encode("utf-8")
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
            "voice": selected_voice,
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
