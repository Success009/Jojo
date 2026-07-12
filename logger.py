import os
import sys
import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows terminal colors
init(autoreset=True)

import os
user_home = os.path.expanduser("~")
LOG_FILE = os.path.join(user_home, ".jojo_system.log")

class Logger:
    @staticmethod
    def _write_to_file(tag, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{tag}] {message}\n")
        except Exception:
            pass

    @staticmethod
    def whisper(message):
        text = f"{Fore.CYAN}{Style.BRIGHT}[WHISPER]{Style.NORMAL} {message}"
        print(text)
        Logger._write_to_file("WHISPER", message)

    @staticmethod
    def groq(message):
        text = f"{Fore.MAGENTA}{Style.BRIGHT}[GROQ]{Style.NORMAL} {message}"
        print(text)
        Logger._write_to_file("GROQ", message)

    @staticmethod
    def browser(message):
        text = f"{Fore.GREEN}{Style.BRIGHT}[BROWSER]{Style.NORMAL} {message}"
        print(text)
        Logger._write_to_file("BROWSER", message)

    @staticmethod
    def system(message):
        text = f"{Fore.YELLOW}{Style.BRIGHT}[SYSTEM]{Style.NORMAL} {message}"
        print(text)
        Logger._write_to_file("SYSTEM", message)

    @staticmethod
    def tool(message):
        text = f"{Fore.BLUE}{Style.BRIGHT}[TOOL]{Style.NORMAL} {message}"
        print(text)
        Logger._write_to_file("TOOL", message)

    @staticmethod
    def agent(message):
        text = f"{Fore.WHITE}{Style.BRIGHT}[AGENT]{Style.NORMAL} {message}"
        print(text)
        Logger._write_to_file("AGENT", message)

    @staticmethod
    def error(message):
        text = f"{Fore.RED}{Style.BRIGHT}[ERROR]{Style.NORMAL} {message}"
        print(text, file=sys.stderr)
        Logger._write_to_file("ERROR", message)

    @staticmethod
    def success(message):
        text = f"{Fore.GREEN}{Style.BRIGHT}[SUCCESS]{Style.NORMAL} {message}"
        print(text)
        Logger._write_to_file("SUCCESS", message)

    @staticmethod
    def divider():
        print(f"{Fore.BLACK}{Style.BRIGHT}" + "="*60)
