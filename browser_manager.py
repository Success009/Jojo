import os
import sys
import time
from playwright.sync_api import sync_playwright
from logger import Logger

class BrowserManager:
    def __init__(self, headless=False, use_pwdebug=False):
        self.headless = headless
        self.use_pwdebug = use_pwdebug
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """
        Starts a headful Playwright Chromium instance.
        If use_pwdebug is True, sets the PWDEBUG environment variable.
        """
        try:
            if self.use_pwdebug:
                os.environ["PWDEBUG"] = "1"
                Logger.browser("Launching Playwright in Debug Mode (PWDEBUG=1)...")
            else:
                # Ensure PWDEBUG is cleared if not requested
                os.environ.pop("PWDEBUG", None)
                Logger.browser("Launching headful Chromium browser...")

            self.playwright = sync_playwright().start()
            
            # Launch Chromium. On Windows, user channel can be 'chrome' or 'msedge' to use local installations
            # but standard chromium packaged with playwright works beautifully too.
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            
            # Create a context with viewport maximized (matching screen size)
            self.context = self.browser.new_context(
                viewport=None,
                no_viewport=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = self.context.new_page()
            Logger.success("Browser launched successfully and page initialized.")
            return True
        except Exception as e:
            Logger.error(f"Failed to start Playwright browser: {e}")
            Logger.system("Ensure 'playwright install' has been executed in the environment.")
            self.close()
            return False

    def open_url(self, url):
        if not self.page:
            if not self.start():
                return "Error: Could not initialize browser."
        
        # Ensure url starts with http/https
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            Logger.browser(f"Navigating to: {url}")
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(1)  # brief wait for initial rendering
            current_url = self.page.url
            title = self.page.title()
            Logger.success(f"Loaded: '{title}' ({current_url})")
            return f"Successfully opened {current_url}. Page title: '{title}'"
        except Exception as e:
            Logger.error(f"Error opening URL {url}: {e}")
            return f"Error opening URL: {e}"

    def click(self, selector):
        if not self.page:
            return "Error: Browser not started."
        try:
            Logger.browser(f"Clicking element: '{selector}'")
            # Try selector directly, or text-based selector
            if selector.startswith("text=") or selector.startswith("role=") or selector.startswith("/") or selector.startswith(".") or selector.startswith("#"):
                self.page.click(selector, timeout=10000)
            else:
                # Attempt to click by CSS or fuzzy text matching
                try:
                    self.page.click(selector, timeout=5000)
                except Exception:
                    # Fallback to text matching
                    self.page.click(f"text={selector}", timeout=5000)
            
            time.sleep(1)
            return f"Clicked element matching: '{selector}'"
        except Exception as e:
            Logger.error(f"Click failed on '{selector}': {e}")
            return f"Click failed: {e}"

    def type_text(self, selector, text, press_enter=False):
        if not self.page:
            return "Error: Browser not started."
        try:
            Logger.browser(f"Typing '{text}' into selector: '{selector}'")
            # Clear existing content first
            self.page.locator(selector).fill("")
            self.page.type(selector, text, delay=50)
            if press_enter:
                time.sleep(0.5)
                self.page.press(selector, "Enter")
                Logger.browser("Pressed Enter key")
            time.sleep(1)
            return f"Successfully typed text into '{selector}'"
        except Exception as e:
            Logger.error(f"Typing failed on '{selector}': {e}")
            return f"Typing failed: {e}"

    def get_browser_state(self):
        if not self.context or not self.page:
            return "Browser is currently closed."
        try:
            pages = self.context.pages
            tab_info = [ ]  # Space inside empty brackets
            for idx, p in enumerate(pages):
                active_str = " (Active)" if p == self.page else ""
                tab_info.append(f"Tab {idx+1}{active_str}: '{p.title()}' - {p.url}")
            return "\n".join(tab_info)
        except Exception as e:
            return f"Error getting browser state: {e}"

    def get_page_summary(self):
        if not self.page:
            return "Error: Browser not started."
        try:
            url = self.page.url
            title = self.page.title()
            text_content = self.page.evaluate("() => document.body.innerText")
            
            # Keep summary extremely compact (first 250 words) to save tokens
            words = text_content.split()
            truncated_text = " ".join(words[:250])
            
            inputs = self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('input, button, select, textarea')).map(el => {
                    return `${el.tagName.toLowerCase()}${el.id ? '#'+el.id : ''} [type="${el.getAttribute('type') || ''}"] [placeholder="${el.getAttribute('placeholder') || ''}"] [text="${(el.innerText || el.value || '').slice(0, 30)}"]`;
                }).slice(0, 15);
            }""")
            
            inputs_summary = "\n".join([f"- {inp}" for inp in inputs])
            
            return (
                f"URL: {url} | Title: {title}\n"
                f"Text snippet: {truncated_text}...\n"
                f"Interactive Elements:\n{inputs_summary}"
            )
        except Exception as e:
            return f"Error extracting page summary: {e}"

    def capture_screenshot(self, filepath=None):
        if not self.page:
            return "Error: Browser not started."
        try:
            if not filepath:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                filepath = os.path.join(script_dir, "browser_screenshot.png")
            self.page.screenshot(path=filepath)
            Logger.success(f"Screenshot saved to: {filepath}")
            return f"Screenshot successfully saved to {filepath}"
        except Exception as e:
            Logger.error(f"Screenshot failed: {e}")
            return f"Screenshot failed: {e}"

    def scroll(self, direction="down", amount=500):
        if not self.page:
            return "Error: Browser not started."
        try:
            Logger.browser(f"Scrolling {direction} by {amount} pixels")
            if direction.lower() == "down":
                self.page.evaluate(f"window.scrollBy(0, {amount})")
            else:
                self.page.evaluate(f"window.scrollBy(0, -{amount})")
            time.sleep(0.5)
            return f"Scrolled {direction} by {amount} pixels"
        except Exception as e:
            return f"Scroll failed: {e}"

    def press_key_combination(self, key_combo):
        if not self.page:
            return "Error: Browser not started."
        try:
            Logger.browser(f"Pressing keyboard combination: '{key_combo}'")
            self.page.keyboard.press(key_combo)
            time.sleep(1)
            return f"Successfully pressed keyboard combination: '{key_combo}'"
        except Exception as e:
            Logger.error(f"Failed to press key combination '{key_combo}': {e}")
            return f"Key press failed: {e}"

    def close(self):
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            Logger.system("Playwright browser shutdown complete.")
        except Exception:
            pass
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
