#!/usr/bin/env python3
"""
TTS/Voice Assistant System - Audit 4 Advanced Features
====================================================

This system provides comprehensive text-to-speech and voice interface capabilities:
- Multiple TTS engines (Azure, Google, OpenAI)
- Voice command recognition
- Natural language processing
- Multi-language support
- Real-time audio processing
- Voice activity detection

Essential for advanced user interaction and accessibility features
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import wave
import tempfile
import io

# Optional imports with fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSEngine(Enum):
    """TTS Engine types"""
    PYTTSX3 = "pyttsx3"
    GTTS = "gtts"
    AZURE = "azure"
    GOOGLE = "google"
    OPENAI = "openai"

class VoiceLanguage(Enum):
    """Supported languages"""
    EN_US = "en-US"
    EN_GB = "en-GB"
    DE_DE = "de-DE"
    FR_FR = "fr-FR"
    ES_ES = "es-ES"
    IT_IT = "it-IT"
    PT_PT = "pt-PT"
    RU_RU = "ru-RU"
    JA_JP = "ja-JP"
    ZH_CN = "zh-CN"

@dataclass
class VoiceConfig:
    """Voice configuration settings"""
    engine: TTSEngine = TTSEngine.PYTTSX3
    language: VoiceLanguage = VoiceLanguage.EN_US
    voice_id: Optional[str] = None
    speed: int = 150
    volume: float = 0.9
    pitch: int = 0
    quality: str = "high"
    output_format: str = "wav"

@dataclass
class AudioConfig:
    """Audio configuration settings"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: int = pyaudio.paInt16
    input_device_index: Optional[int] = None
    output_device_index: Optional[int] = None

@dataclass
class VoiceCommand:
    """Voice command structure"""
    command: str
    confidence: float
    timestamp: datetime
    language: VoiceLanguage
    handler: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

class VoiceActivityDetector:
    """
    Voice Activity Detection (VAD) system
    """
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.is_recording = False
        self.audio_buffer = []
        self.silence_threshold = 500
        self.silence_duration = 2.0
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def detect_voice_activity(self, audio_data: bytes) -> bool:
        """Detect voice activity in audio data"""
        try:
            if not HAS_NUMPY:
                # Fallback: simple amplitude detection
                amplitude = sum(abs(byte) for byte in audio_data) / len(audio_data)
                return amplitude > self.silence_threshold
            
            # Convert audio data to amplitude
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            amplitude = np.abs(audio_array).mean()
            
            return amplitude > self.silence_threshold
            
        except Exception as e:
            self.logger.error(f"Voice activity detection error: {e}")
            return False
    
    def start_recording(self) -> None:
        """Start voice activity detection"""
        self.is_recording = True
        self.audio_buffer = []
        self.logger.info("Voice activity detection started")
    
    def stop_recording(self) -> bytes:
        """Stop recording and return audio data"""
        self.is_recording = False
        audio_data = b''.join(self.audio_buffer)
        self.audio_buffer = []
        self.logger.info("Voice activity detection stopped")
        return audio_data

class TextToSpeechEngine:
    """
    Text-to-Speech engine with multiple backend support
    """
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.engine = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize TTS engine
        self._initialize_engine()
    
    def _initialize_engine(self) -> None:
        """Initialize the TTS engine"""
        try:
            if self.config.engine == TTSEngine.PYTTSX3:
                self._initialize_pyttsx3()
            elif self.config.engine == TTSEngine.GTTS:
                self._initialize_gtts()
            elif self.config.engine == TTSEngine.AZURE:
                self._initialize_azure()
            elif self.config.engine == TTSEngine.GOOGLE:
                self._initialize_google()
            elif self.config.engine == TTSEngine.OPENAI:
                self._initialize_openai()
            else:
                raise ValueError(f"Unsupported TTS engine: {self.config.engine}")
            
            self.logger.info(f"TTS engine initialized: {self.config.engine.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            # Fallback to pyttsx3
            self._initialize_pyttsx3()
    
    def _initialize_pyttsx3(self) -> None:
        """Initialize pyttsx3 engine"""
        if not HAS_PYTTSX3:
            raise ImportError("pyttsx3 not installed")
            
        self.engine = pyttsx3.init()
        
        # Set voice properties
        voices = self.engine.getProperty('voices')
        if voices:
            # Select voice based on language
            for voice in voices:
                if self.config.language.value in voice.id:
                    self.engine.setProperty('voice', voice.id)
                    break
            else:
                # Use first available voice
                self.engine.setProperty('voice', voices[0].id)
        
        # Set speech rate
        self.engine.setProperty('rate', self.config.speed)
        
        # Set volume
        self.engine.setProperty('volume', self.config.volume)
    
    def _initialize_gtts(self) -> None:
        """Initialize Google TTS"""
        # gTTS doesn't require initialization
        pass
    
    def _initialize_azure(self) -> None:
        """Initialize Azure Cognitive Services TTS"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Get Azure credentials from environment
            speech_key = os.getenv('AZURE_SPEECH_KEY')
            speech_region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
            
            if not speech_key:
                raise ValueError("Azure Speech key not found in environment")
            
            # Create speech config
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=speech_region
            )
            
            # Set voice
            speech_config.speech_synthesis_voice_name = self._get_azure_voice()
            
            self.engine = speechsdk.SpeechSynthesizer(speech_config=speech_config)
            
        except ImportError:
            self.logger.error("Azure Speech SDK not installed")
            raise
        except Exception as e:
            self.logger.error(f"Azure TTS initialization error: {e}")
            raise
    
    def _initialize_google(self) -> None:
        """Initialize Google Cloud TTS"""
        try:
            from google.cloud import texttospeech
            
            # Initialize client
            self.engine = texttospeech.TextToSpeechClient()
            
        except ImportError:
            self.logger.error("Google Cloud TTS not installed")
            raise
        except Exception as e:
            self.logger.error(f"Google TTS initialization error: {e}")
            raise
    
    def _initialize_openai(self) -> None:
        """Initialize OpenAI TTS"""
        try:
            import openai
            
            # Get OpenAI API key
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found in environment")
            
            openai.api_key = api_key
            self.engine = openai
            
        except ImportError:
            self.logger.error("OpenAI library not installed")
            raise
        except Exception as e:
            self.logger.error(f"OpenAI TTS initialization error: {e}")
            raise
    
    def synthesize_speech(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            output_file: Optional output file path
            
        Returns:
            Audio data as bytes if output_file is None
        """
        try:
            if self.config.engine == TTSEngine.PYTTSX3:
                return self._synthesize_pyttsx3(text, output_file)
            elif self.config.engine == TTSEngine.GTTS:
                return self._synthesize_gtts(text, output_file)
            elif self.config.engine == TTSEngine.AZURE:
                return self._synthesize_azure(text, output_file)
            elif self.config.engine == TTSEngine.GOOGLE:
                return self._synthesize_google(text, output_file)
            elif self.config.engine == TTSEngine.OPENAI:
                return self._synthesize_openai(text, output_file)
            else:
                raise ValueError(f"Unsupported TTS engine: {self.config.engine}")
                
        except Exception as e:
            self.logger.error(f"Speech synthesis error: {e}")
            return None
    
    def _synthesize_pyttsx3(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Synthesize speech using pyttsx3"""
        if output_file:
            self.engine.save_to_file(text, output_file)
            self.engine.runAndWait()
            return None
        else:
            # For in-memory synthesis, save to temp file and read
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                self.engine.save_to_file(text, tmp.name)
                self.engine.runAndWait()
                
                with open(tmp.name, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(tmp.name)
                return audio_data
    
    def _synthesize_gtts(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Synthesize speech using Google TTS"""
        lang = self.config.language.value.split('-')[0]  # Convert en-US to en
        
        tts = gTTS(text=text, lang=lang, slow=False)
        
        if output_file:
            tts.save(output_file)
            return None
        else:
            # Save to memory buffer
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
    
    def _synthesize_azure(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Synthesize speech using Azure TTS"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            result = self.engine.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data
                
                if output_file:
                    with open(output_file, 'wb') as f:
                        f.write(audio_data)
                    return None
                else:
                    return audio_data
            else:
                self.logger.error(f"Azure TTS synthesis failed: {result.reason}")
                return None
                
        except ImportError:
            self.logger.error("Azure Speech SDK not installed")
            return None
        except Exception as e:
            self.logger.error(f"Azure TTS synthesis error: {e}")
            return None
    
    def _synthesize_google(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Synthesize speech using Google Cloud TTS"""
        try:
            from google.cloud import texttospeech
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.config.language.value,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16
            )
            
            response = self.engine.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            if output_file:
                with open(output_file, 'wb') as f:
                    f.write(response.audio_content)
                return None
            else:
                return response.audio_content
                
        except Exception as e:
            self.logger.error(f"Google TTS synthesis error: {e}")
            return None
    
    def _synthesize_openai(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Synthesize speech using OpenAI TTS"""
        try:
            response = self.engine.Audio.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            audio_data = response.content
            
            if output_file:
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                return None
            else:
                return audio_data
                
        except Exception as e:
            self.logger.error(f"OpenAI TTS synthesis error: {e}")
            return None
    
    def _get_azure_voice(self) -> str:
        """Get Azure voice name for the configured language"""
        voice_map = {
            VoiceLanguage.EN_US: "en-US-AriaNeural",
            VoiceLanguage.EN_GB: "en-GB-SoniaNeural",
            VoiceLanguage.DE_DE: "de-DE-KatjaNeural",
            VoiceLanguage.FR_FR: "fr-FR-DeniseNeural",
            VoiceLanguage.ES_ES: "es-ES-ElviraNeural",
            VoiceLanguage.IT_IT: "it-IT-ElsaNeural",
            VoiceLanguage.PT_PT: "pt-PT-RaquelNeural",
            VoiceLanguage.RU_RU: "ru-RU-SvetlanaNeural",
            VoiceLanguage.JA_JP: "ja-JP-NanamiNeural",
            VoiceLanguage.ZH_CN: "zh-CN-XiaoxiaoNeural"
        }
        
        return voice_map.get(self.config.language, "en-US-AriaNeural")

class SpeechRecognitionEngine:
    """
    Speech recognition engine with multiple backend support
    """
    
    def __init__(self, audio_config: AudioConfig):
        self.audio_config = audio_config
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(
            device_index=audio_config.input_device_index,
            sample_rate=audio_config.sample_rate,
            chunk_size=audio_config.chunk_size
        )
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Calibrate for ambient noise
        self._calibrate_microphone()
    
    def _calibrate_microphone(self) -> None:
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                self.logger.info("Microphone calibrated for ambient noise")
        except Exception as e:
            self.logger.error(f"Microphone calibration error: {e}")
    
    def recognize_speech(self, audio_data: Optional[bytes] = None, 
                        language: VoiceLanguage = VoiceLanguage.EN_US) -> Optional[str]:
        """
        Recognize speech from audio data or microphone
        
        Args:
            audio_data: Audio data to recognize (if None, uses microphone)
            language: Language for recognition
            
        Returns:
            Recognized text or None if recognition failed
        """
        try:
            if audio_data:
                # Recognize from audio data
                audio = sr.AudioData(audio_data, self.audio_config.sample_rate, 2)
            else:
                # Recognize from microphone
                with self.microphone as source:
                    self.logger.info("Listening for speech...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Recognize using Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language=language.value)
            self.logger.info(f"Recognized speech: {text}")
            return text
            
        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timeout")
            return None
        except sr.UnknownValueError:
            self.logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Speech recognition error: {e}")
            return None
    
    def continuous_recognition(self, callback: Callable[[str], None],
                             language: VoiceLanguage = VoiceLanguage.EN_US) -> None:
        """
        Continuous speech recognition with callback
        
        Args:
            callback: Function to call with recognized text
            language: Language for recognition
        """
        def recognition_callback(recognizer, audio):
            try:
                text = recognizer.recognize_google(audio, language=language.value)
                callback(text)
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                self.logger.error(f"Speech recognition service error: {e}")
        
        # Start background listening
        stop_listening = self.recognizer.listen_in_background(
            self.microphone, recognition_callback
        )
        
        self.logger.info("Continuous speech recognition started")
        return stop_listening

class VoiceCommandProcessor:
    """
    Voice command processing and routing system
    """
    
    def __init__(self):
        self.commands = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def register_command(self, command: str, handler: Callable[[Dict[str, Any]], Any],
                        description: str = "") -> None:
        """
        Register a voice command handler
        
        Args:
            command: Command phrase or pattern
            handler: Function to handle the command
            description: Command description
        """
        self.commands[command.lower()] = {
            'handler': handler,
            'description': description
        }
        self.logger.info(f"Registered voice command: {command}")
    
    def process_command(self, text: str, confidence: float = 1.0) -> Optional[Any]:
        """
        Process recognized speech text as a command
        
        Args:
            text: Recognized speech text
            confidence: Recognition confidence
            
        Returns:
            Command result or None if no command matched
        """
        try:
            text_lower = text.lower().strip()
            
            # Find matching command
            for command, info in self.commands.items():
                if command in text_lower:
                    self.logger.info(f"Executing command: {command}")
                    
                    # Extract parameters
                    parameters = self._extract_parameters(text_lower, command)
                    
                    # Create voice command
                    voice_command = VoiceCommand(
                        command=command,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        language=VoiceLanguage.EN_US,
                        handler=info['handler'],
                        parameters=parameters
                    )
                    
                    # Execute command
                    result = info['handler'](voice_command)
                    return result
            
            self.logger.warning(f"No command found for: {text}")
            return None
            
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            return None
    
    def _extract_parameters(self, text: str, command: str) -> Dict[str, Any]:
        """Extract parameters from command text"""
        # Simple parameter extraction - can be enhanced with NLP
        parameters = {}
        
        # Remove the command from text to get parameters
        remaining_text = text.replace(command, '').strip()
        
        if remaining_text:
            parameters['text'] = remaining_text
        
        return parameters
    
    def list_commands(self) -> List[Dict[str, str]]:
        """List all registered commands"""
        return [
            {
                'command': command,
                'description': info['description']
            }
            for command, info in self.commands.items()
        ]

class VoiceAssistant:
    """
    Main voice assistant system integrating TTS, STT, and command processing
    """
    
    def __init__(self, voice_config: VoiceConfig = None, audio_config: AudioConfig = None):
        self.voice_config = voice_config or VoiceConfig()
        self.audio_config = audio_config or AudioConfig()
        
        # Initialize components
        self.tts_engine = TextToSpeechEngine(self.voice_config)
        self.stt_engine = SpeechRecognitionEngine(self.audio_config)
        self.command_processor = VoiceCommandProcessor()
        self.vad = VoiceActivityDetector(self.audio_config)
        
        self.is_listening = False
        self.is_speaking = False
        self.conversation_history = []
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Register default commands
        self._register_default_commands()
    
    def _register_default_commands(self) -> None:
        """Register default voice commands"""
        self.command_processor.register_command(
            "hello", self._handle_hello, "Greet the assistant"
        )
        self.command_processor.register_command(
            "time", self._handle_time, "Get current time"
        )
        self.command_processor.register_command(
            "date", self._handle_date, "Get current date"
        )
        self.command_processor.register_command(
            "help", self._handle_help, "Get help information"
        )
        self.command_processor.register_command(
            "stop", self._handle_stop, "Stop the assistant"
        )
        self.command_processor.register_command(
            "status", self._handle_status, "Get system status"
        )
    
    def speak(self, text: str, interrupt: bool = False) -> bool:
        """
        Speak text using TTS
        
        Args:
            text: Text to speak
            interrupt: Whether to interrupt current speech
            
        Returns:
            True if speech was successful
        """
        try:
            if self.is_speaking and not interrupt:
                self.logger.warning("Already speaking, use interrupt=True to override")
                return False
            
            self.is_speaking = True
            self.logger.info(f"Speaking: {text}")
            
            # Synthesize speech
            audio_data = self.tts_engine.synthesize_speech(text)
            
            if audio_data:
                # Play audio (implementation depends on platform)
                self._play_audio(audio_data)
                
                # Add to conversation history
                self.conversation_history.append({
                    'type': 'assistant',
                    'text': text,
                    'timestamp': datetime.now()
                })
                
                return True
            else:
                self.logger.error("Failed to synthesize speech")
                return False
                
        except Exception as e:
            self.logger.error(f"Speech error: {e}")
            return False
        finally:
            self.is_speaking = False
    
    def listen(self, timeout: float = 5.0) -> Optional[str]:
        """
        Listen for speech input
        
        Args:
            timeout: Timeout for listening
            
        Returns:
            Recognized text or None
        """
        try:
            self.is_listening = True
            self.logger.info("Listening for speech...")
            
            # Recognize speech
            text = self.stt_engine.recognize_speech(language=self.voice_config.language)
            
            if text:
                self.logger.info(f"Heard: {text}")
                
                # Add to conversation history
                self.conversation_history.append({
                    'type': 'user',
                    'text': text,
                    'timestamp': datetime.now()
                })
                
                return text
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Listening error: {e}")
            return None
        finally:
            self.is_listening = False
    
    def process_voice_command(self, text: str) -> Optional[Any]:
        """Process voice command"""
        return self.command_processor.process_command(text)
    
    def start_conversation(self) -> None:
        """Start interactive conversation mode"""
        self.logger.info("Starting conversation mode")
        self.speak("Hello! I'm your voice assistant. How can I help you?")
        
        try:
            while True:
                # Listen for user input
                user_input = self.listen()
                
                if user_input:
                    # Process as command
                    result = self.process_voice_command(user_input)
                    
                    if result is None:
                        # If no command matched, provide general response
                        self.speak("I'm sorry, I didn't understand that command. Say 'help' for available commands.")
                    
                    # Check for stop command
                    if "stop" in user_input.lower():
                        break
                else:
                    # No input detected
                    self.speak("I didn't hear anything. Please try again.")
                    
        except KeyboardInterrupt:
            self.logger.info("Conversation interrupted by user")
        except Exception as e:
            self.logger.error(f"Conversation error: {e}")
        finally:
            self.speak("Goodbye!")
    
    def _play_audio(self, audio_data: bytes) -> None:
        """Play audio data (platform-specific implementation needed)"""
        # This is a placeholder - actual implementation depends on platform
        # For Windows: use winsound
        # For Linux: use aplay or similar
        # For macOS: use afplay
        pass
    
    def _handle_hello(self, command: VoiceCommand) -> str:
        """Handle hello command"""
        response = "Hello! How can I help you today?"
        self.speak(response)
        return response
    
    def _handle_time(self, command: VoiceCommand) -> str:
        """Handle time command"""
        current_time = datetime.now().strftime("%I:%M %p")
        response = f"The current time is {current_time}"
        self.speak(response)
        return response
    
    def _handle_date(self, command: VoiceCommand) -> str:
        """Handle date command"""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        response = f"Today is {current_date}"
        self.speak(response)
        return response
    
    def _handle_help(self, command: VoiceCommand) -> str:
        """Handle help command"""
        commands = self.command_processor.list_commands()
        response = "Available commands: " + ", ".join([cmd['command'] for cmd in commands])
        self.speak(response)
        return response
    
    def _handle_stop(self, command: VoiceCommand) -> str:
        """Handle stop command"""
        response = "Stopping the voice assistant. Goodbye!"
        self.speak(response)
        return response
    
    def _handle_status(self, command: VoiceCommand) -> str:
        """Handle status command"""
        response = "Voice assistant is running and ready to help!"
        self.speak(response)
        return response
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared")

def main():
    """Main function for testing the voice assistant"""
    try:
        # Create voice assistant with default configuration
        assistant = VoiceAssistant()
        
        print("Voice Assistant System - Test Mode")
        print("=" * 40)
        
        # Test TTS
        print("Testing Text-to-Speech...")
        assistant.speak("Hello, this is a test of the voice assistant system.")
        
        # Test command processing
        print("Testing command processing...")
        test_commands = [
            "hello",
            "what time is it",
            "what's the date",
            "help",
            "status"
        ]
        
        for cmd in test_commands:
            print(f"Processing command: {cmd}")
            result = assistant.process_voice_command(cmd)
            print(f"Result: {result}")
            time.sleep(1)
        
        print("\nVoice assistant test completed!")
        
    except Exception as e:
        print(f"Error in voice assistant: {e}")
        logger.error(f"Voice assistant error: {e}")

if __name__ == "__main__":
    main()
