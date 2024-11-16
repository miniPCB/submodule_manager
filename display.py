import os

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_welcome():
    """Display a welcome message and menu options."""
    clear_screen()
    print("==========================")
    print("  Submodule Manager Tool  ")
    print("==========================")
    print("1. Scan, select, install and remove submodules")
    print("2. Update installed submodules")
    print("3. Exit")
    return input("Enter your choice: ").strip()