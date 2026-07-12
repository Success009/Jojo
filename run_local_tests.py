import os
import sys

# Add projects/Jojo to path to ensure modules are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import Logger
from test_suite import test_groq_rotation, test_context_manager

if __name__ == "__main__":
    Logger.divider()
    Logger.system("STARTING AUTOMATED MODULE VERIFICATION")
    Logger.divider()
    
    context_ok = test_context_manager()
    Logger.divider()
    
    groq_ok = test_groq_rotation()
    Logger.divider()
    
    if context_ok and groq_ok:
        Logger.success("Core modules verified successfully!")
        sys.exit(0)
    else:
        Logger.error("Module verification failed.")
        sys.exit(1)
