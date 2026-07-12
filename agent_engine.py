import json
import re
import subprocess
from logger import Logger
from groq_client import GroqRotator
from context_manager import ContextManager
from browser_manager import BrowserManager

SYSTEM_PROMPT = """You are Jojo, a highly capable, fast, and personable Windows AI system assistant.
You possess a helpful, friendly, and energetic personality.
You are running on a powerful machine with an AMD Ryzen 7000 series CPU and 16GB of RAM.

=== SYSTEM CAPABILITIES & BEHAVIOR ===
1. TOKEN CONSERVATION: You understand token efficiency. Keep thoughts and reasoning incredibly brief and focused. Avoid verbose explanations.
2. MULTI-STEP RECURSION & RECOVERY: You can perform multiple actions sequentially. If an action fails (e.g. element not found), DO NOT retry the exact same action. Instead, adapt: scroll the page, use alternative selectors, query Google, or run a shell command to gather information.
3. CONTEXT AWARENESS: You maintain scrollable history and a Splash Pad (scratchpad) containing user info, system settings, and key facts. Keep notes in the Splash Pad updated!
4. TOOL EXECUTION: You must run tools using a single JSON block. You MUST only run ONE tool per turn, then wait for the environment's response.
5. NO WRITING CODE: You are not a developer tool. Focus on web navigation, local command execution, system interaction, and helping the user directly.

=== TOOL CALL FORMAT (MANDATORY JSON) ===
When you want to run a tool, output a single markdown JSON block containing "action" and "arguments" keys. Do not output anything else if you are calling a tool.

Example Format:
```json
{
  "action": "browser_open",
  "arguments": {
    "url": "https://example.com"
  }
}
```

Available Tools:

1. Open Webpage:
{ "action": "browser_open", "arguments": { "url": "https://example.com" } }

2. Click Element on Page:
{ "action": "browser_click", "arguments": { "selector": "button_or_text_or_css" } }

3. Type Text into Element:
{ "action": "browser_type", "arguments": { "selector": "input_css", "text": "my query", "press_enter": true } }

4. Get Current Page Summary (reads text & interactive elements):
{ "action": "browser_get_summary", "arguments": { } }

5. Scroll Page:
{ "action": "browser_scroll", "arguments": { "direction": "down", "amount": 500 } }

6. Capture Screenshot:
{ "action": "browser_screenshot", "arguments": { } }

7. Run Windows Command (runs in cmd.exe):
{ "action": "run_terminal_command", "arguments": { "command": "dir" } }

8. Update Splash Pad / Scratchpad Fact:
{ "action": "update_splash_pad", "arguments": { "key": "user_name", "value": "Alice" } }

9. Press Keyboard Combination (e.g. Control+V, Enter, Control+A, Tab):
{ "action": "browser_press_key", "arguments": { "key_combo": "Control+V" } }

10. Copy Local File to Windows Clipboard (ideal for copying images/documents to paste into social media, chats, or emails):
{ "action": "copy_file_to_clipboard", "arguments": { "filepath": "C:\\path\\to\\image.png" } }

11. Finish / Respond to User (Use this when the task is complete):
{ "action": "finish", "arguments": { "response": "Your final answer or report goes here." } }

=== HOW TO SEND FILES/IMAGES TO CHATS (E.G. MESSENGER) ===
To send a file to a chat, first run "copy_file_to_clipboard" with the local file path. Then click on the chat box using "browser_click", and finally run "browser_press_key" with argument "Control+V" followed by "Enter"! This makes sending attachments flawless.

Ensure that you formulate your actions step-by-step. Remember, the user is looking at the headful browser window you control!
"""

class JojoAgentEngine:
    def __init__(self, use_pwdebug=False):
        self.rotator = GroqRotator()
        self.context = ContextManager()
        self.browser = BrowserManager(headless=False, use_pwdebug=use_pwdebug)
        self.max_steps = 8

    def run_command_locally(self, command):
        """Runs a command on Windows cmd shell securely."""
        Logger.tool(f"Executing Windows shell command: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=20
            )
            output = result.stdout
            if result.stderr:
                output += f"\nError Output:\n{result.stderr}"
            if not output.strip():
                output = "Command executed successfully with no stdout output."
            return output
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 20 seconds."
        except Exception as e:
            return f"Error executing command: {e}"

    def parse_tool_call(self, response_text):
        """Parses the JSON tool call from markdown block or raw JSON string."""
        # Search for ```json ... ``` blocks
        block_match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
        try:
            if block_match:
                json_str = block_match.group(1).strip()
                return json.loads(json_str)
            
            # Fallback: look for any JSON-like dict pattern { "action": ... }
            fallback_match = re.search(r"\{\s*\"action\"\s*:\s*.*\}", response_text, re.DOTALL)
            if fallback_match:
                return json.loads(fallback_match.group(0).strip())
        except Exception:
            pass
        return None

    def shutdown(self):
        self.browser.close()

    def process_instruction(self, instruction):
        """
        Runs Jojo's multi-step decision loop for a single user instruction.
        Recurses up to self.max_steps.
        """
        Logger.agent(f"Starting processing loop for instruction: '{instruction}'")
        self.context.add_message("user", instruction)
        
        step = 0
        while step < self.max_steps:
            step += 1
            Logger.agent(f"=== Agent Step {step}/{self.max_steps} ===")
            
            # Prepare API Payload
            api_messages = self.context.get_messages_for_api(SYSTEM_PROMPT)
            
            # Query Groq 70B via the rotator
            try:
                response = self.rotator.send_chat_completion(api_messages, model="llama-3.3-70b-versatile")
            except Exception as e:
                Logger.error(f"Failed to query Groq model: {e}")
                return "Error: Unable to connect to Groq backend."
            
            Logger.agent(f"Jojo's Response:\n{response}")
            
            # Add assistant response to history
            self.context.add_message("assistant", response)
            
            # Parse tool call
            tool = self.parse_tool_call(response)
            if not tool or "action" not in tool:
                # If no tool is called but text is returned, assume final response
                Logger.system("No JSON tool block detected. Treating response as final text.")
                return response

            tool_name = tool["action"]
            arguments = tool.get("arguments", { })  # Space inside empty brackets
            
            Logger.tool(f"Calling Tool: '{tool_name}' with arguments {arguments}")
            tool_result = ""
            
            if tool_name == "browser_open":
                url = arguments.get("url", "")
                tool_result = self.browser.open_url(url)
                
            elif tool_name == "browser_click":
                selector = arguments.get("selector", "")
                tool_result = self.browser.click(selector)
                
            elif tool_name == "browser_type":
                selector = arguments.get("selector", "")
                text = arguments.get("text", "")
                press_enter = arguments.get("press_enter", False)
                tool_result = self.browser.type_text(selector, text, press_enter)
                
            elif tool_name == "browser_get_summary":
                tool_result = self.browser.get_page_summary()
                
            elif tool_name == "browser_scroll":
                direction = arguments.get("direction", "down")
                try:
                    amount = int(arguments.get("amount", 500))
                except ValueError:
                    amount = 500
                tool_result = self.browser.scroll(direction, amount)
                
            elif tool_name == "browser_screenshot":
                tool_result = self.browser.capture_screenshot()
                
            elif tool_name == "run_terminal_command":
                cmd = arguments.get("command", "")
                tool_result = self.run_command_locally(cmd)
                
            elif tool_name == "update_splash_pad":
                k = arguments.get("key", "")
                v = arguments.get("value", "")
                self.context.update_splash_pad_fact(k, v)
                tool_result = f"Splash pad updated successfully: {k} is now {v}."

            elif tool_name == "browser_press_key":
                key_combo = arguments.get("key_combo", "")
                tool_result = self.browser.press_key_combination(key_combo)

            elif tool_name == "copy_file_to_clipboard":
                fp = arguments.get("filepath", "")
                abs_p = os.path.abspath(fp)
                cmd = f'powershell -Command "Set-Clipboard -Path \'{abs_p}\'"'
                tool_result = self.run_command_locally(cmd)
                
            elif tool_name == "finish":
                final_resp = arguments.get("response", "Task completed.")
                Logger.success(f"Agent finished task: {final_resp}")
                return final_resp
                
            else:
                tool_result = f"Error: Tool '{tool_name}' is not recognized."
                Logger.error(tool_result)
                
            # Log result of tool and add to assistant context
            Logger.success(f"Tool execution result (truncated): {tool_result[:150]}...")
            self.context.add_message("user", f"Tool '{tool_name}' execution result:\n{tool_result}")
            
        Logger.error("Max recursion steps reached without a final answer.")
        return "Task took too long to complete. (Recursion depth limit reached)."
