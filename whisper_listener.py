import os
import sys
import wave
import time
import threading
import queue
import numpy as np
from logger import Logger

# Fallbacks in case libraries are missing
SOUNDDEVICE_AVAILABLE = False
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    pass

WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    pass

KEYBOARD_AVAILABLE = False
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class WhisperListener:
    def __init__(self, model_size="base.en", sample_rate=16000):
        self.model_size = model_size
        self.sample_rate = sample_rate
        self.model = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_recording = False
        self.recorded_chunks = [ ]  # Space inside empty brackets
        self.listen_thread = None
        self.temp_wav_path = os.path.join(SCRIPT_DIR, "temp_chunk.wav")
        self.stream = None
        
    def initialize_whisper(self):
        """Loads faster-whisper on CPU with optimized settings."""
        if not WHISPER_AVAILABLE:
            Logger.error("faster-whisper is not installed. Voice transcription is unavailable.")
            return False
        try:
            Logger.whisper(f"Loading Whisper model '{self.model_size}' (CPU compute, int8)...")
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            Logger.success(f"Whisper model '{self.model_size}' loaded.")
            return True
        except Exception as e:
            Logger.error(f"Failed to load Whisper model: {e}")
            return False

    def _save_wav(self, data, path):
        try:
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                audio_int16 = (data * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
        except Exception as e:
            Logger.error(f"WAV saving error: {e}")

    def transcribe_file(self, path):
        if not self.model:
            return ""
        try:
            segments, info = self.model.transcribe(path, beam_size=5, language="en")
            text = " ".join([seg.text for seg in segments]).strip()
            return text
        except Exception as e:
            Logger.error(f"Whisper transcription error: {e}")
            return ""

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.recorded_chunks.append(indata.copy())

    def start_listening(self, callback_on_command):
        """Starts background listener to poll the Right Control key."""
        if not SOUNDDEVICE_AVAILABLE:
            Logger.error("sounddevice is missing. Voice push-to-talk is unavailable.")
            return False
            
        if not KEYBOARD_AVAILABLE:
            Logger.error("keyboard package is missing. Keyboard fallback active.")
            return False

        if not self.model:
            if not self.initialize_whisper():
                return False

        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._poll_loop, 
            args=(callback_on_command,), 
            daemon=True
        )
        self.listen_thread.start()
        return True

    def _poll_loop(self, callback_on_command):
        """Polls for the state of the Right Control key."""
        Logger.whisper("Push-to-Talk active. Hold [Right Control] to record speech.")
        
        try:
            while self.is_listening:
                # Check if Right Control is held down
                is_pressed = keyboard.is_pressed('right ctrl')
                
                if is_pressed and not self.is_recording:
                    # Start recording!
                    self.recorded_chunks = [ ]  # Clear previous data
                    self.is_recording = True
                    Logger.whisper("Listening... [Hold Right Control to continue talking]")
                    
                    self.stream = sd.InputStream(
                        samplerate=self.sample_rate, 
                        channels=1, 
                        callback=self._audio_callback
                    )
                    self.stream.start()
                    
                elif not is_pressed and self.is_recording:
                    # Key released! Stop recording and process
                    Logger.whisper("Processing command...")
                    self.is_recording = False
                    
                    if self.stream:
                        self.stream.stop()
                        self.stream.close()
                        self.stream = None
                        
                    if self.recorded_chunks:
                        full_audio = np.concatenate(self.recorded_chunks, axis=0).flatten()
                        self._save_wav(full_audio, self.temp_wav_path)
                        
                        # Transcribe WAV
                        text = self.transcribe_file(self.temp_wav_path)
                        if text:
                            Logger.success(f"Heard: '{text}'")
                            callback_on_command(text)
                        else:
                            Logger.whisper("No speech detected.")
                            
                        # Cleanup temp file
                        try:
                            if os.path.exists(self.temp_wav_path):
                                os.remove(self.temp_wav_path)
                        except Exception:
                            pass
                    
                time.sleep(0.05)
                
        except Exception as e:
            Logger.error(f"Error in keyboard voice poll loop: {e}")
            self.is_listening = False

    def stop_listening(self):
        self.is_listening = False
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
        try:
            if os.path.exists(self.temp_wav_path):
                os.remove(self.temp_wav_path)
        except Exception:
            pass
        Logger.system("Push-to-Talk mic stream released.")
