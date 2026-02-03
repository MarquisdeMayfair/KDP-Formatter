"""Text-to-speech for draft review audio."""
from __future__ import annotations

from pathlib import Path

from app.config import settings


class TTSService:
    """Generate audio for draft chapters."""

    async def generate_audio(self, text: str, output_path: str) -> str:
        provider = settings.tts_provider.lower()
        if provider == "edge":
            return await self._generate_edge(text, output_path)
        if provider == "elevenlabs":
            return await self._generate_elevenlabs(text, output_path)
        raise ValueError(f"Unsupported TTS provider: {settings.tts_provider}")

    async def _generate_edge(self, text: str, output_path: str) -> str:
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("edge-tts is not installed. Install it or switch provider.") from exc

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(text, voice="en-GB-RyanNeural")
        await communicate.save(output_path)
        return output_path

    async def _generate_elevenlabs(self, text: str, output_path: str) -> str:
        if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
            raise ValueError("ElevenLabs settings are missing.")

        import httpx

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
        headers = {"xi-api-key": settings.elevenlabs_api_key}
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 0.75,
                "speed": 1.05,
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.content

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as handle:
            handle.write(data)
        return output_path
