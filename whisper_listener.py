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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class WhisperListener:
    def __init__(self, model_size="base.en", activation_word="hey jojo", sample_rate=16000):
        self.model_size = model_size
        self.activation_word = activation_word.lower()
        self.sample_rate = sample_rate
        self.model = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.listen_thread = None
        self.is_active = False # True when wake word is triggered and we are capturing command
        self.temp_wav_path = os.path.join(SCRIPT_DIR, "temp_chunk.wav")
        
    def initialize_whisper(self):
        """
        Loads the faster-whisper model in memory (CPU or CUDA).
        On Ryzen 7000 + 16GB RAM, 'base.en' on CPU (using float32 or int8) is super fast.
        """
        if not WHISPER_AVAILABLE:
            Logger.error("faster-whisper is not installed. Whisper listening will be unavailable.")
            return False
        
        try:
            Logger.whisper(f"Loading local Whisper model '{self.model_size}' (CPU compute)...")
            # Ryzen 7000 has great AVX-512. CPU execution with int8 or float32 is optimal
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            Logger.success(f"Whisper model '{self.model_size}' loaded successfully.")
            return True
        except Exception as e:
            Logger.error(f"Failed to load Whisper model: {e}")
            return False

    def _save_wav(self, data, path):
        """Saves numpy audio array to a standard 16kHz mono WAV file."""
        try:
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                # Convert float32 back to int16
                audio_int16 = (data * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
        except Exception as e:
            Logger.error(f"WAV saving error: {e}")

    def transcribe_file(self, path):
        """Transcribes audio file using faster-whisper and returns the complete text."""
        if not self.model:
            return ""
        try:
            segments, info = self.model.transcribe(path, beam_size=5, language="en")
            text = " ".join([seg.text for seg in segments]).strip()
            return text
        except Exception as e:
            Logger.error(f"Whisper transcription error: {e}")
            return ""

    def contains_wake_word(self, text):
        """
        Checks if the transcribed text matches the wake word variations.
        Handles common typos/pronunciations: 'hey jojo', 'hay jojo', 'jojo', 'hi jojo', 'jo jo'.
        """
        cleaned = text.lower().replace(",", "").replace(".", "").replace("!", "").strip()
        variations = ["hey jojo", "hay jojo", "hey jo jo", "hi jojo", "hi jo jo", "jojo", "jo jo"]
        
        for var in variations:
            if var in cleaned:
                return True
        return False

    def _audio_callback(self, indata, frames, time_info, status):
        """This is called for each audio block by sounddevice."""
        if status:
            pass
        self.audio_queue.put(indata.copy())

    def start_listening(self, callback_on_command):
        """
        Starts a background thread to listen to the microphone.
        When wake word and command are successfully resolved, calls callback_on_command(command_text).
        """
        if not SOUNDDEVICE_AVAILABLE:
            Logger.error("sounddevice not available. Keyboard-input fallback will be used.")
            return False

        if not self.model:
            if not self.initialize_whisper():
                Logger.error("Could not load Whisper model. Keyboard fallback will be used.")
                return False

        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._listen_loop, 
            args=(callback_on_command,), 
            daemon=True
        )
        self.listen_thread.start()
        Logger.whisper("Background voice listening active. Say 'Hey Jojo' to start!")
        return True

    def _listen_loop(self, callback_on_command):
        """
        Background voice activity detection loop.
        Listens to 3-second buffer sliding chunks.
        If wake word is detected, switches to record mode to capture user instructions.
        """
        # Settings for listening loop
        buffer_size_seconds = 3
        silence_threshold = 0.015 # simple amplitude energy threshold
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate, 
                channels=1, 
                callback=self._audio_callback
            ):
                Logger.whisper("Microphone streams connected.")
                audio_buffer = [ ] # Space inside brackets
                
                while self.is_listening:
                    # Collect data from queue
                    while not self.audio_queue.empty():
                        chunk = self.audio_queue.get()
                        audio_buffer.append(chunk)

                    # We want to process audio in ~3 second blocks
                    total_samples = sum(len(c) for c in audio_buffer)
                    if total_samples >= self.sample_rate * buffer_size_seconds:
                        # Flatten buffer
                        full_chunk = np.concatenate(audio_buffer, axis=0).flatten()
                        audio_buffer = [ ] # Reset buffer
                        
                        # Calculate volume/energy
                        energy = np.sqrt(np.mean(full_chunk**2))
                        
                        if energy > silence_threshold:
                            self._save_wav(full_chunk, self.temp_wav_path)
                            transcription = self.transcribe_file(self.temp_wav_path)
                            
                            if transcription:
                                Logger.whisper(f"Heard (background): '{transcription}' (energy: {energy:.4f})")
                                
                                if self.contains_wake_word(transcription):
                                    Logger.success("WAKE WORD DETECTED! 'Hey Jojo' active.")
                                    # Now record the command (next 6 seconds of speech)
                                    Logger.whisper("Recording your command... Speak now!")
                                    
                                    # Sleep to record command block (6 seconds)
                                    time.sleep(6.0)
                                    
                                    # Drain queue to capture command
                                    cmd_chunks = [ ] # Space inside brackets
                                    while not self.audio_queue.empty():
                                        cmd_chunks.append(self.audio_queue.get())
                                        
                                    if cmd_chunks:
                                        cmd_audio = np.concatenate(cmd_chunks, axis=0).flatten()
                                        self._save_wav(cmd_audio, self.temp_wav_path)
                                        command_text = self.transcribe_file(self.temp_wav_path)
                                        
                                        if command_text:
                                            Logger.success(f"Command Captured: '{command_text}'")
                                            # Trigger callback
                                            callback_on_command(command_text)
                                        else:
                                            Logger.whisper("No speech detected in command chunk.")
                                    else:
                                        Logger.whisper("No audio received for command.")
                                        
                        # Clear temp files
                        try:
                            if os.path.exists(self.temp_wav_path):
                                os.remove(self.temp_wav_path)
                        except Exception:
                            pass
                    
                    time.sleep(0.1)
                    
        except Exception as e:
            Logger.error(f"Error in Whisper listening stream: {e}")
            self.is_listening = False

    def stop_listening(self):
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
        # Cleanup temp file
        try:
            if os.path.exists(self.temp_wav_path):
                os.remove(self.temp_wav_path)
        except Exception:
            pass
        Logger.system("Whisper background listener stopped. Audio hardware released.")
