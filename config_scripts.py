import json
import os
import subprocess

def load_config(file_path):
    """Load the JSON configuration file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file '{file_path}' not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {}

def save_config(file_path, data):
    """Save the configuration file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Configuration saved to {file_path}")
    except Exception as e:
        print(f"Error saving configuration: {e}")

def edit_config(file_path):
    """Open the JSON configuration file for editing."""
    try:
        editor = os.getenv("EDITOR", "nano" if os.name != "nt" else "notepad")
        subprocess.run([editor, file_path])
    except Exception as e:
        print(f"Failed to open editor: {str(e)}")