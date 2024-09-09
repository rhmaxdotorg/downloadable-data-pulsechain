#!/usr/bin/env python3
# Helper for running Python scripts across different operating systems

import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

def find_python_executable():
    python_executables = ['python', 'python3', 'py']
    
    path = os.environ.get('PATH', '')

    for exe in python_executables:
        try:
            result = subprocess.run([exe, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                return exe
        except FileNotFoundError:
            pass
    
    logger.error("No Python executable found. Please ensure Python is installed and in your PATH.")
    logger.error("You may need to restart your command prompt or system after installation.")
    return None

def run_python_script(script_name, *args):
    python_exe = find_python_executable()
    if not python_exe:
        sys.exit(1)

    try:
        result = subprocess.run([python_exe, script_name] + list(args),
                                capture_output=True, text=True, check=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        logger.error(f"Command output: {e.output}")
        return False
    except FileNotFoundError:
        logger.error(f"{script_name} not found in the current directory.")
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"Directory contents: {os.listdir('.')}")
        return False
