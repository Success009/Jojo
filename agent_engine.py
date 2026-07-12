import re
import os
import subprocess
from logger import Logger
from groq_client import GroqRotator
from context_manager import ContextManager
from browser_manager import BrowserManager

SYSTEM_PROMPT = """You are Jojo, a highly capable, fast, and personable Windows AI system assistant.
You possess a helpful, friendly, and energetic personality.
You are running on a powerful machine with an AMD Ryzen 7000 series CPU and 16GB of RAM.

=== SYSTEM CAPABILITIES & BEHAVIOR ===
1. TOKEN CONSERVATION: You understand token efficiency. Keep thoughts and reasoning incredibly brief and focused.
2. DISCIPLINED ACTION: Perform EXACTLY what is requested, no more and no less. Do not perform extra unrequested tasks.
3. IMMEDIATE COMPLETION: Once you have successfully completed the requested task, you MUST immediately call the "finish" tool. Do not hallucinate or repeat actions.
4. CONTEXT AWARENESS: You maintain a Splash Pad (scratchpad) containing user info, system settings, and key facts. Keep notes in the Splash Pad updated!
5. TOOL EXECUTION: You must run tools using a single compact <t> XML block. You MUST only run ONE tool per turn, then wait for the environment's response.
6. NO WRITING CODE: You are not a developer tool. Focus on web navigation, local command execution, system interaction, and helping the user directly.

=== TOOL CALL FORMAT (MANDATORY <t> XML) ===
When you want to run a tool, output a single <t> block containing an <action> tag and argument tags. Do not output anything else if you are calling a tool.

Example Format:
<t>
  <action>browser_open</action>
  <url>https://example.com</url>
</t>

Available Tools:

1. Open Webpage:
<t>
  <action>browser_open</action>
  <url>https://example.com</url>
</t>

2. Click Element on Page:
<t>
  <action>browser_click</action>
  <selector>button_or_text_or_css</selector>
</t>

3. Type Text into Element:
<t>
  <action>browser_type</action>
  <selector>input_css</selector>
  <text>my query</text>
  <press_enter>true</press_enter> <!-- or false -->
</t>

4. Get Current Page Summary (reads text & interactive elements):
<t>
  <action>browser_get_summary</action>
</t>

5. Scroll Page:
<t>
  <action>browser_scroll</action>
  <direction>down</direction> <!-- or up -->
  <amount>500</amount>
</t>

6. Capture Screenshot:
<t>
  <action>browser_screenshot</action>
</t>

7. Run Windows Command (runs in cmd.exe):
<t>
  <action>run_terminal_command</action>
  <command>dir</command>
</t>

8. Update Splash Pad / Scratchpad Fact:
<t>
  <action>update_splash_pad</action>
  <key>user_name</key>
  <value>Alice</value>
</t>

9. Press Keyboard Combination (e.g. Control+V, Enter, Control+A, Tab):
<t>
  <action>browser_press_key</action>
  <key_combo>Control+V</key_combo>
</t>

10. Copy Local File to Windows Clipboard (ideal for copying images/documents to paste into social media, chats, or emails):
<t>
  <action>copy_file_to_clipboard</action>
  <filepath>C:\\path\\to\\image.png</filepath>
</t>

11. Finish / Respond to User (Use this IMMEDIATELY when the task is completed):
<t>
  <action>finish</action>
  <response>Your final answer or report goes here.</response>
</t>

=== HOW TO SEND FILES/IMAGES TO CHATS (E.G. MESSENGER) ===
To send a file to a chat, first run "copy_file_to_clipboard" with the local file path. Then click on the chat box using "browser_click", and finally run "browser_press_key" with argument "Control+V" followed by "Enter"!

Remember, the user is looking at the headful browser window you control!
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
        """Parses the compact <t> XML tool call structure."""
        # Find block between <t> and </t>
        t_match = re.search(r"<t>(.*?)</t>", response_text, re.DOTALL)
        if not t_match:
            return None
            
        block_content = t_match.group(1).strip()
        
        # Extract action
        action_match = re.search(r"<action>(.*?)</action>", block_content, re.DOTALL)
        if not action_match:
            return None
            
        tool_name = action_match.group(1).strip()
        arguments = { }  # Space inside empty brackets
        
        # Extract general argument tags inside the <t> block
        tags = ["url", "selector", "text", "press_enter", "direction", "amount", "command", "key", "value", "key_combo", "filepath", "response"]
        for tag in tags:
            tag_match = re.search(f"<{tag}>(.*?)</{tag}>", block_content, re.DOTALL)
            if tag_match:
                arguments[tag] = tag_match.group(1).strip()
                
        return {"action": tool_name, "arguments": arguments}

    def shutdown(self):
        self.browser.close()

    def process_instruction(self, instruction):
        """
        Runs Jojo's multi-step decision loop for a single user instruction.
        Clears conversation history at the start to prevent old task interference.
        Recurses up to self.max_steps.
        """
        # Ensure fresh context sandbox for this task
        self.context.clear_history()
        
        Logger.agent(f"Starting isolated task: '{instruction}'")
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
                Logger.system("No XML tool block <t> detected. Treating response as final text.")
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
                press_enter = arguments.get("press_enter", "false").lower() == "true"
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
