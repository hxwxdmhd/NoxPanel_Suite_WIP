"""
🎤 Voice Interface for NoxAssistant
==================================

Provides voice recognition and text-to-speech capabilities
inspired by J.A.R.V.I.S. and S.A.T.U.R.D.A.Y. implementations.

Features:
- Wake word detection
- Continuous voice monitoring
- Natural language processing
- ADHD-friendly voice responses
- Offline voice recognition options
"""

import threading
import time
import queue
import logging
from typing import Optional, Callable, Dict, Any

# Voice dependencies (optional)
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceInterface:
    """
    🎤 Voice Interface for NoxAssistant
    
    Handles voice recognition, text-to-speech, and continuous monitoring
    with wake word detection similar to J.A.R.V.I.S. and S.A.T.U.R.D.A.Y.
    """
    
    def __init__(self, wake_words: list = None, voice_settings: Dict[str, Any] = None):
        if not VOICE_AVAILABLE:
            raise ImportError("Voice capabilities not available. Install: pip install SpeechRecognition pyttsx3")
        
        self.wake_words = wake_words or ["hey nox", "nox", "assistant", "jarvis"]
        self.voice_settings = voice_settings or {}
        
        # Voice recognition setup
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Text-to-speech setup
        self.tts_engine = self.setup_tts_engine()
        
        # Threading for continuous monitoring
        self.listening = False
        self.voice_queue = queue.Queue()
        self.listen_thread = None
        
        # Callbacks
        self.command_callback: Optional[Callable] = None
        self.wake_callback: Optional[Callable] = None
        
        # Performance tuning
        self.setup_recognition_settings()
        
    def setup_tts_engine(self):
        """Initialize and configure text-to-speech engine"""
        try:
            engine = pyttsx3.init()
            
            # Voice selection - prefer female voice for pleasantness
            voices = engine.getProperty('voices')
            if voices:
                for voice in voices:
                    voice_name = voice.name.lower()
                    if any(name in voice_name for name in ['zira', 'hazel', 'female']):
                        engine.setProperty('voice', voice.id)
                        logger.info(f"Selected voice: {voice.name}")
                        break
            
            # Speech rate optimization for ADHD-friendly experience
            rate = self.voice_settings.get('rate', 180)  # Slightly slower than default
            engine.setProperty('rate', rate)
            
            # Volume settings
            volume = self.voice_settings.get('volume', 0.8)
            engine.setProperty('volume', volume)
            
            return engine
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            return None
    
    def setup_recognition_settings(self):
        """Optimize speech recognition settings"""
        try:
            # Adjust for ambient noise
            with self.microphone as source:
                logger.info("🎤 Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                
            # Recognition settings for better accuracy
            self.recognizer.energy_threshold = 4000  # Adjust based on environment
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8  # Seconds of silence before phrase ends
            self.recognizer.phrase_threshold = 0.3  # Minimum seconds of speaking audio
            
            logger.info("✅ Voice recognition configured")
            
        except Exception as e:
            logger.error(f"Failed to configure voice recognition: {e}")
    
    def speak(self, text: str, interrupt: bool = True):
        """
        Convert text to speech with ADHD-friendly pacing
        
        Args:
            text: Text to speak
            interrupt: Whether to interrupt current speech
        """
        if not self.tts_engine:
            return
            
        try:
            if interrupt:
                self.tts_engine.stop()
            
            # Clean text for better speech synthesis
            cleaned_text = self.clean_text_for_speech(text)
            
            logger.info(f"🗣️ Speaking: {cleaned_text}")
            self.tts_engine.say(cleaned_text)
            self.tts_engine.runAndWait()
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
    
    def clean_text_for_speech(self, text: str) -> str:
        """
        Clean text for better speech synthesis
        
        Args:
            text: Raw text with markdown and emojis
            
        Returns:
            Cleaned text suitable for speech
        """
        # Remove emojis
        import re
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                 u"\U0001F1E0-\U0001F1FF"  # flags
                                 u"\U00002702-\U000027B0"
                                 u"\U000024C2-\U0001F251"
                                 "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # Remove markdown formatting
        text = text.replace('**', '').replace('*', '').replace('`', '')
        text = text.replace('###', '').replace('##', '').replace('#', '')
        
        # Replace technical terms with speech-friendly versions
        replacements = {
            'CPU': 'C P U',
            'RAM': 'R A M',
            'API': 'A P I',
            'HTTP': 'H T T P',
            'URL': 'U R L',
            'AI': 'A I',
            'IP': 'I P address',
            'DNS': 'D N S',
            'SSL': 'S S L'
        }
        
        for tech_term, speech_version in replacements.items():
            text = text.replace(tech_term, speech_version)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listen for a single voice command
        
        Args:
            timeout: Maximum time to wait for speech
            phrase_time_limit: Maximum time for a single phrase
            
        Returns:
            Recognized text or None
        """
        try:
            with self.microphone as source:
                logger.debug("🎤 Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
            # Try multiple recognition engines for better accuracy
            recognized_text = None
            
            try:
                # Google Speech Recognition (requires internet)
                recognized_text = self.recognizer.recognize_google(audio)
                logger.info(f"📝 Google recognized: {recognized_text}")
            except (sr.UnknownValueError, sr.RequestError):
                pass
            
            if not recognized_text:
                try:
                    # Sphinx for offline recognition (if available)
                    recognized_text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"📝 Sphinx recognized: {recognized_text}")
                except (sr.UnknownValueError, sr.RequestError):
                    pass
            
            return recognized_text.lower() if recognized_text else None
            
        except sr.WaitTimeoutError:
            logger.debug("⏰ Listen timeout - no speech detected")
            return None
        except Exception as e:
            logger.error(f"Voice recognition error: {e}")
            return None
    
    def detect_wake_word(self, text: str) -> bool:
        """
        Check if text contains a wake word
        
        Args:
            text: Recognized text to check
            
        Returns:
            True if wake word detected
        """
        if not text:
            return False
            
        text_lower = text.lower()
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                logger.info(f"🎯 Wake word detected: {wake_word}")
                return True
        return False
    
    def continuous_listen(self):
        """
        Continuously listen for wake words and commands
        Background thread function
        """
        logger.info("👂 Starting continuous listening...")
        
        while self.listening:
            try:
                # Listen for wake word with shorter timeout
                audio_input = self.listen_once(timeout=2, phrase_time_limit=5)
                
                if audio_input:
                    if self.detect_wake_word(audio_input):
                        # Wake word detected
                        if self.wake_callback:
                            self.wake_callback()
                        
                        self.speak("Yes? How can I help you?")
                        
                        # Listen for actual command with longer timeout
                        command = self.listen_once(timeout=10, phrase_time_limit=15)
                        
                        if command:
                            logger.info(f"🎯 Command received: {command}")
                            if self.command_callback:
                                self.command_callback(command)
                        else:
                            self.speak("I didn't catch that. Try again.")
                            
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                logger.error(f"Continuous listening error: {e}")
                time.sleep(1)  # Longer delay on error
    
    def start_listening(self, command_callback: Callable = None, wake_callback: Callable = None):
        """
        Start continuous voice monitoring
        
        Args:
            command_callback: Function to call with recognized commands
            wake_callback: Function to call when wake word detected
        """
        if self.listening:
            logger.warning("Voice interface already listening")
            return
        
        self.command_callback = command_callback
        self.wake_callback = wake_callback
        
        self.listening = True
        self.listen_thread = threading.Thread(target=self.continuous_listen, daemon=True)
        self.listen_thread.start()
        
        logger.info("🎤 Voice interface started")
    
    def stop_listening(self):
        """Stop continuous voice monitoring"""
        self.listening = False
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        
        logger.info("🛑 Voice interface stopped")
    
    def interactive_session(self, assistant_callback: Callable):
        """
        Run an interactive voice session
        
        Args:
            assistant_callback: Function to process commands and return responses
        """
        self.speak("Hello! I'm NoxAssistant. Say 'Hey Nox' to get my attention, or 'exit' to quit.")
        
        try:
            while True:
                # Listen for wake word or direct command
                user_input = self.listen_once(timeout=30)  # Longer timeout for interactive mode
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if any(exit_word in user_input for exit_word in ["exit", "quit", "goodbye", "bye"]):
                    self.speak("Goodbye! Have a great day!")
                    break
                
                # Check for wake word
                if self.detect_wake_word(user_input):
                    self.speak("Yes, how can I help you?")
                    
                    # Listen for actual command
                    command = self.listen_once(timeout=15)
                    if command:
                        user_input = command
                    else:
                        self.speak("I didn't hear anything. Try again.")
                        continue
                
                # Process command
                try:
                    response = assistant_callback(user_input)
                    
                    # Extract key information for speech
                    speech_response = self.extract_speech_summary(response)
                    self.speak(speech_response)
                    
                except Exception as e:
                    logger.error(f"Command processing error: {e}")
                    self.speak("Sorry, I encountered an error processing that command.")
                    
        except KeyboardInterrupt:
            self.speak("Session interrupted. Goodbye!")
        except Exception as e:
            logger.error(f"Interactive session error: {e}")
            self.speak("I'm experiencing technical difficulties. Goodbye!")
    
    def extract_speech_summary(self, response: str) -> str:
        """
        Extract key information from response for speech synthesis
        
        Args:
            response: Full text response
            
        Returns:
            Summarized version suitable for speech
        """
        lines = response.split('\n')
        
        # Extract key points and summaries
        speech_lines = []
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and formatting
            if not line or line.startswith('=') or line.startswith('-'):
                continue
            
            # Include headers and important information
            if any(keyword in line.lower() for keyword in ['summary', 'status', 'found', 'error', 'warning', 'tip']):
                speech_lines.append(line)
            
            # Include first few bullet points
            if line.startswith('•') or line.startswith('-'):
                if len(speech_lines) < 8:  # Limit to prevent too long speech
                    speech_lines.append(line)
        
        # If no specific content found, use first few lines
        if not speech_lines:
            speech_lines = [line for line in lines[:5] if line.strip()]
        
        result = '. '.join(speech_lines)
        
        # Limit length for reasonable speech duration
        if len(result) > 500:
            result = result[:500] + "... For more details, check the display."
        
        return result

# CLI interface for testing voice capabilities
def main():
    """Test voice interface capabilities"""
    if not VOICE_AVAILABLE:
        print("❌ Voice capabilities not available. Install requirements:")
        print("   pip install SpeechRecognition pyttsx3")
        return
    
    print("🎤 Testing NoxAssistant Voice Interface")
    print("=" * 50)
    
    # Test TTS
    voice = VoiceInterface()
    voice.speak("Hello! Voice interface is working correctly.")
    
    # Test voice recognition
    print("\n🎤 Say something to test voice recognition (5 seconds):")
    result = voice.listen_once(timeout=5)
    
    if result:
        print(f"✅ Recognized: {result}")
        voice.speak(f"I heard you say: {result}")
    else:
        print("❌ No speech detected")
        voice.speak("I didn't hear anything")
    
    # Test wake word detection
    test_phrases = [
        "hey nox how are you",
        "nox check the system",
        "just some random text",
        "assistant help me"
    ]
    
    print("\n🎯 Testing wake word detection:")
    for phrase in test_phrases:
        detected = voice.detect_wake_word(phrase)
        print(f"  '{phrase}': {'✅ Detected' if detected else '❌ Not detected'}")

if __name__ == "__main__":
    main()
