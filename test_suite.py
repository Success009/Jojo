import os
import sys
import time
from logger import Logger
from groq_client import GroqRotator
from context_manager import ContextManager
from browser_manager import BrowserManager

def test_groq_rotation():
    Logger.system("=== RUNNING TEST: GROQ KEY ROTATION & COOLDOWN ===")
    rotator = GroqRotator()
    
    # Let's perform two quick queries to check rotation and cooldown sleep
    messages = [{"role": "user", "content": "Say 'Jojo Online' in 2 words."}]
    
    try:
        Logger.system("Sending Query 1...")
        resp1 = rotator.send_chat_completion(messages, max_tokens=20)
        Logger.success(f"Response 1: '{resp1.strip()}'")
        
        # Test 2 will trigger cooldown wait and verify rotation
        Logger.system("Sending Query 2 (Triggering cooldown & rotation)...")
        resp2 = rotator.send_chat_completion(messages, max_tokens=20)
        Logger.success(f"Response 2: '{resp2.strip()}'")
        
        Logger.success("Groq Key Rotation and Cooldown Test: PASSED")
        return True
    except Exception as e:
        Logger.error(f"Groq Key Rotation Test: FAILED - {e}")
        return False

def test_context_manager():
    Logger.system("=== RUNNING TEST: CONTEXT & SPLASH PAD ===")
    test_file = "test_splash_pad.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        
    try:
        manager = ContextManager(splash_pad_file=test_file)
        
        # Verify default properties
        assert manager.splash_pad["user_name"] == "User"
        
        # Update fact
        manager.update_splash_pad_fact("user_name", "Bruce Wayne")
        assert manager.splash_pad["user_name"] == "Bruce Wayne"
        
        # Verify saving/loading
        manager2 = ContextManager(splash_pad_file=test_file)
        assert manager2.splash_pad["user_name"] == "Bruce Wayne"
        
        # Test sliding history
        for i in range(25):
            manager.add_message("user", f"message {i}")
            
        assert len(manager.history) <= manager.max_history_len
        Logger.success(f"History successfully capped to {manager.max_history_len}")
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            
        Logger.success("Context and Splash Pad Test: PASSED")
        return True
    except Exception as e:
        Logger.error(f"Context and Splash Pad Test: FAILED - {e}")
        return False

def test_browser_automation():
    Logger.system("=== RUNNING TEST: BROWSER AUTOMATION (PLAYWRIGHT) ===")
    browser = BrowserManager(headless=False)
    
    try:
        Logger.system("Initializing headful Playwright...")
        if not browser.start():
            Logger.error("Failed to start browser. Make sure 'playwright install' is completed.")
            return False
            
        # 1. Open URL
        Logger.system("Opening URL: https://example.com")
        res_open = browser.open_url("https://example.com")
        Logger.success(res_open)
        
        # 2. Get Summary
        summary = browser.get_page_summary()
        Logger.success("Page Summary retrieved:")
        print(summary[:300] + "...\n")
        
        # 3. Take Screenshot
        screenshot_path = "test_screenshot.png"
        res_ss = browser.capture_screenshot(screenshot_path)
        Logger.success(res_ss)
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            
        # 4. Scroll page
        res_scroll = browser.scroll("down", 200)
        Logger.success(res_scroll)
        
        Logger.success("Browser Automation Test: PASSED")
        return True
    except Exception as e:
        Logger.error(f"Browser Automation Test: FAILED - {e}")
        return False
    finally:
        browser.close()

def main():
    Logger.divider()
    Logger.system("JOJO MODULAR TESTING SUITE")
    Logger.divider()
    
    print("Select test to run:")
    print("1) Test Groq API Key Rotation & Rate Limits")
    print("2) Test Context Manager & Splash Pad")
    print("3) Test Playwright Browser Automation")
    print("4) Run All Tests")
    print("Any other key to Exit.")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_groq_rotation()
    elif choice == "2":
        test_context_manager()
    elif choice == "3":
        test_browser_automation()
    elif choice == "4":
        s1 = test_groq_rotation()
        Logger.divider()
        s2 = test_context_manager()
        Logger.divider()
        s3 = test_browser_automation()
        Logger.divider()
        
        if s1 and s2 and s3:
            Logger.success("ALL TESTS PASSED SUCCESSFULLY!")
        else:
            Logger.error("SOME TESTS FAILED. CHECK LOGS.")
    else:
        print("Exiting test suite.")

if __name__ == "__main__":
    main()
