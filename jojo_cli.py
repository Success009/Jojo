import os
import sys
import time
from colorama import init, Fore, Style
from logger import Logger
from agent_engine import JojoAgentEngine
from whisper_listener import WhisperListener

# Initialize colorama
init(autoreset=True)

BANNER = f"""
{Fore.YELLOW}{Style.BRIGHT}      _  ____      _  ____      
     | |/ __ \\    | |/ __ \\     
  _  | | |  | | _ | | |  | |    
 | |_| | |__| || |_| | |__| |   
  \\___/ \\____/  \\___/ \\____/    
{Fore.CYAN}{Style.BRIGHT}
       === JOJO AI COMPANION ===
    Highly Capable Local Developer Assistant
    Windows System, Ryzen 7000, 16GB RAM
"""

def print_banner():
    print(BANNER)
    Logger.divider()
    Logger.system("System Initialized. Keys configured.  rate-limit delay active.")
    Logger.divider()

def main():
    print_banner()
    
    # Initialize Agent Engine
    # Supports PWDEBUG flag in env or CLI
    use_debug = "--debug" in sys.argv
    engine = JojoAgentEngine(use_pwdebug=use_debug)
    
    # Initialize Whisper
    listener = WhisperListener()
    
    # Callback when whisper hears a valid command
    def on_whisper_command(cmd_text):
        Logger.divider()
        Logger.agent(f"Processing Voice Command: '{cmd_text}'")
        try:
            response = engine.process_instruction(cmd_text)
            Logger.divider()
            Logger.success(f"Response to voice command: {response}")
            Logger.divider()
        except Exception as e:
            Logger.error(f"Failed to process voice command: {e}")
            
    # Try starting Whisper
    whisper_active = False
    try:
        Logger.system("Attempting to start local Whisper Voice Listening...")
        if listener.start_listening(on_whisper_command):
            whisper_active = True
            Logger.success("Whisper Listening Stream is online!")
        else:
            Logger.error("Whisper listener could not start due to missing audio dependencies.")
    except Exception as e:
        Logger.error(f"Error starting Whisper listener: {e}")

    if not whisper_active:
        Logger.system("Running Jojo in KEYBOARD INPUT FALLBACK MODE.")
        Logger.system("You can type instructions directly below.")
        Logger.divider()
    else:
        Logger.system("Jojo is listening to your mic for 'Hey Jojo' commands!")
        Logger.system("You can also type instructions below at any time.")
        Logger.divider()

    # Main Interactive Command Loop
    try:
        while True:
            try:
                prompt_text = f"\n{Fore.GREEN}{Style.BRIGHT}Jojo User > {Style.RESET_ALL}"
                user_input = input(prompt_text).strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ["exit", "quit", "bye", "close"]:
                    Logger.system("Exiting Jojo. Thank you!")
                    break
                    
                if user_input.lower() == "clear":
                    engine.context.clear_history()
                    continue
                    
                Logger.divider()
                # Run the agent instruction loop
                response = engine.process_instruction(user_input)
                Logger.divider()
                Logger.success(f"Jojo Response:\n{response}")
                Logger.divider()
                
            except KeyboardInterrupt:
                print()
                Logger.system("Interrupted by user (Ctrl+C). Cleaning up and closing...")
                break
            except Exception as e:
                Logger.error(f"An unexpected error occurred: {e}")
                
    finally:
        # Graceful cleanup and memory release
        Logger.system("Initiating graceful shutdown...")
        if whisper_active:
            try:
                listener.stop_listening()
            except Exception as e:
                Logger.error(f"Failed to stop Whisper listener: {e}")
                
        try:
            engine.shutdown()
        except Exception as e:
            Logger.error(f"Failed to shut down browser/agent: {e}")
            
        Logger.success("Jojo shutdown completely. Memory cleared. Have a great day!")
        sys.exit(0)

if __name__ == "__main__":
    main()
