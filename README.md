# Jojo AI Companion - Windows System Assistant

Jojo is a modular, fast local Windows assistant optimized for AMD Ryzen 7000 and 16GB RAM. It controls headful Playwright Chromium, executes native shell utilities, processes on-demand Push-To-Talk voice commands, and rotates through 10 Groq keys calling `llama-3.3-70b-versatile` with high token efficiency.

---

## 🗺️ Project Directory Map & Anchors

Before making changes, refer to these file anchors:

1. **`jojo_cli.py`**: The CLI orchestrator. Handles boot, dashboard layout, keyboard polling, and clean shutdown.
2. **`bin/jojo.js`**: Global launcher. Resolves paths via `~/.jojo_config.json`, runs auto-update checks (`git pull`), and spawns python.
3. **`agent_engine.py`**: The decision agent. Contains the system prompt, parses compact `<t>` XML tool blocks, and handles real-time keyboard interrupts.
4. **`whisper_listener.py`**: Voice manager. Records audio *only* when the user holds [Right Control]. Transcribes with local `faster-whisper` (`base.en` in `int8` CPU mode).
5. **`browser_manager.py`**: Playwright browser controller. Performs clicks, navigation, typing, key combinations, and compiles compact page text summaries.
6. **`context_manager.py`**: Context keeper. Manages rolling turn history (10 turns) and persistent scratchpad facts inside `~/.jojo_splash_pad.json`.
7. **`logger.py`**: Color styles logging inside `~/.jojo_system.log`.
8. **`groq_client.py`**: API Key rotator. Cycles 10 keys and enforces a  global request cooldown.
9. **`install_jojo.bat`**: Zero-click CMD setup. Creates `venv`, pulls updates, installs deps, and npm-links the global command.

---

## 🛠️ Key Safeguards & Guidelines

- **On-Demand Audio (No Leakage)**: Microphone is never kept open. Audio is recorded only when [Right Control] is held down. Temp audio is saved to `tempfile.gettempdir()` to avoid System32 permission limits.
- **Auto-Updates**: The launcher writes the source path to `~/.jojo_config.json`. Every time `jojo` is run, it pulls updates silently from GitHub, ensuring your friend is always in sync.
- **Interruption**: If Jojo is running a multi-step task, holding down [Right Control] instantly halts the loop.
- **No Unverified Assumptions**: Developers must read the corresponding file anchor first before writing code or making modifications.
- **XML Tools**: Jojo expects compact `<t>` XML structures:
  ```xml
  <t>
    <action>browser_open</action>
    <url>https://example.com</url>
  </t>
  ```

---

## 📥 Clean Reinstall Command

Copy and run this single-line command in CMD or PowerShell as Administrator:

```cmd
cd %USERPROFILE%\Desktop && npm uninstall -g jojo-cli && rmdir /s /q Jojo 2>nul & git clone https://github.com/Success009/Jojo.git && cd Jojo && install_jojo.bat
```
Once done, run `jojo` globally!