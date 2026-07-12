#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');

// Constants
const SCRIPT_DIR = path.dirname(__dirname); // parent folder of bin
const LOCK_FILE_PATH = path.join(os.tmpdir(), 'jojo_instance.lock');

// 1. Prevents duplicate running instances using cross-platform lock files
function acquireLock() {
    if (fs.existsSync(LOCK_FILE_PATH)) {
        try {
            const oldPidStr = fs.readFileSync(LOCK_FILE_PATH, 'utf8').trim();
            const oldPid = parseInt(oldPidStr, 10);
            if (!isNaN(oldPid)) {
                // Cross-platform check if process exists (signal 0 doesn't kill it)
                process.kill(oldPid, 0);
                
                // Process is alive!
                console.error(`\x1b[31m[ERROR] Jojo is already running in another window (PID: ${oldPid}).\x1b[0m`);
                console.error(`\x1b[33mTo prevent audio and browser resource conflicts, please close the other instance.\x1b[0m`);
                process.exit(1);
            }
        } catch (e) {
            // If process.kill throws an error, the process is dead (ESRCH), so we can overwrite the lock.
            if (e.code !== 'ESRCH') {
                console.error(`Failed to verify lock file status: ${e.message}`);
            }
        }
    }
    
    // Write new PID
    fs.writeFileSync(LOCK_FILE_PATH, process.pid.toString(), 'utf8');
}

function releaseLock() {
    try {
        if (fs.existsSync(LOCK_FILE_PATH)) {
            const pidStr = fs.readFileSync(LOCK_FILE_PATH, 'utf8').trim();
            if (pidStr === process.pid.toString()) {
                fs.unlinkSync(LOCK_FILE_PATH);
            }
        }
    } catch (e) {
        // Ignore unlink errors
    }
}

// 2. Locate the python executable
function getPythonPath() {
    // Check local virtual environment first
    const isWindows = os.platform() === 'win32';
    const venvPythonWin = path.join(SCRIPT_DIR, 'venv', 'Scripts', 'python.exe');
    const venvPythonUnix = path.join(SCRIPT_DIR, 'venv', 'bin', 'python');
    
    if (isWindows && fs.existsSync(venvPythonWin)) {
        return venvPythonWin;
    } else if (!isWindows && fs.existsSync(venvPythonUnix)) {
        return venvPythonUnix;
    }
    
    // Fallback to system Python
    return isWindows ? 'python' : 'python3';
}

function main() {
    acquireLock();
    
    const pythonExe = getPythonPath();
    const cliScript = path.join(SCRIPT_DIR, 'jojo_cli.py');
    const args = [cliScript, ...process.argv.slice(2)];
    
    console.log(`\x1b[33m[LAUNCHER] Starting Jojo process using ${pythonExe}...\x1b[0m`);
    
    const child = spawn(pythonExe, args, {
        cwd: SCRIPT_DIR,
        stdio: 'inherit' // Direct terminal pipe for colors, logs, and keyboard input
    });
    
    // Register clean exit hooks
    child.on('exit', (code) => {
        releaseLock();
        process.exit(code || 0);
    });
    
    process.on('SIGINT', () => {
        // Let child handle the SIGINT signal gracefully
        releaseLock();
    });
    
    process.on('exit', () => {
        releaseLock();
    });
}

main();
