"""NoxCore Voice Interface Module - Speech Recognition & TTS"""

try:
    from .speech_engine import SpeechEngine
except ImportError:
    SpeechEngine = None

try:
    from .wake_word_detector import WakeWordDetector
except ImportError:
    WakeWordDetector = None

try:
    from .tts_engine import TTSEngine
except ImportError:
    TTSEngine = None

__version__ = "1.0.0"
__all__ = ['SpeechEngine', 'WakeWordDetector', 'TTSEngine']

# Voice Interface Configuration
VOICE_CONFIG = {
    "wake_word": "hey nox",
    "speech_timeout": 5.0,
    "phrase_timeout": 1.0,
    "energy_threshold": 4000,
    "dynamic_energy_threshold": True,
    "tts_voice_rate": 200,
    "tts_voice_volume": 0.8,
    "microphone_index": None,  # Auto-detect
    "language": "en-US"
}
