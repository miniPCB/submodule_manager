import os
import json
import subprocess
import requests
import shutil

from display import display_welcome, clear_screen
from config_scripts import load_config, save_config, edit_config
from submodule_functions import get_existing_submodules, scan_existing_submodule_paths, add_or_update_submodule

# Path to your JSON configuration file
CONFIG_FILE = "submodules.json"
GITHUB_CONFIG_FILE = "config.json"
SUBMODULE_DIRECTORY = "submodules"

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

def fetch_github_repositories():
    """Fetch GitHub repositories of the authenticated user."""
    try:
        with open(GITHUB_CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)
            token = config.get('github_token')

        if not token:
            print("GitHub token not found in config.json.")
            return []

        url = 'https://api.github.com/user/repos'
        headers = {'Authorization': f'token {token}'}

        repos_data = []
        page = 1

        while True:
            response = requests.get(f'{url}?page={page}&per_page=100', headers=headers)

            if response.status_code != 200:
                print(f"Failed to fetch repositories: {response.status_code} - {response.text}")
                break

            repos = response.json()

            if not repos:
                break

            repos_data.extend(repos)
            page += 1

        return repos_data
    except Exception as e:
        print(f"Error fetching GitHub repositories: {str(e)}")
        return []

def scan_and_update_submodules():
    """Scan for repositories, select, and update submodules."""
    repos = fetch_github_repositories()
    if not repos:
        print("No repositories found.")
        return

    print("Scanning for existing repositories...")
    existing_repos = scan_existing_submodule_paths()

    print("Found the following existing repositories:")
    for repo in existing_repos:
        print(f"  - {repo}")

    config = load_config(CONFIG_FILE)
    toggle_repo_selection(repos, config)

def toggle_repo_selection(repos, config):
    """Display and allow toggling of repository selection."""
    selected_repos = config.get("submodules", [])
    selected_paths = {repo["path"] for repo in selected_repos}
    existing_repos = scan_existing_submodule_paths()

    repo_status = {repo['name']: (repo['name'] in existing_repos) for repo in repos}

    while True:
        print("\nAvailable Repositories:")
        for idx, (name, selected) in enumerate(repo_status.items(), start=1):
            status = "[X]" if selected else "[ ]"
            print(f"{idx}. {status} {name}")

        choice = input("Enter the number to toggle selection, 'update' to sync changes, or 'done' to finish: ").strip()

        if choice.lower() == 'done':
            break

        if choice.lower() == 'update':
            print("Updating repositories based on selection...")
            updated_submodules = []
            for repo in repos:
                if repo_status[repo['name']]:
                    updated_submodules.append({
                        "path": os.path.join(SUBMODULE_DIRECTORY, repo['name']),
                        "url": repo['clone_url'],
                        "branch": "main"  # Assuming 'main' as the default branch
                    })

            config["submodules"] = updated_submodules
            save_config(CONFIG_FILE, config)
            sync_existing_submodules()
            print("Update completed!")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(repos):
                repo_name = list(repo_status.keys())[idx]
                repo_status[repo_name] = not repo_status[repo_name]
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Invalid input. Enter a number, 'update', or 'done'.")

def sync_existing_submodules():
    """Update all existing submodules."""
    print("Syncing all existing submodules...")
    try:
        subprocess.run(["git", "submodule", "update", "--init", "--remote"], check=True)
        print("All submodules are up to date.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to sync submodules: {e.stderr or str(e)}")

def remove_submodule(path):
    """Remove a submodule and update .gitmodules."""
    print(f"Attempting to remove submodule: {path}")
    try:
        # Deinitialize the submodule
        subprocess.run(["git", "submodule", "deinit", "-f", path], check=True)
        # Remove the submodule from the .gitmodules file
        subprocess.run(["git", "rm", "-f", path], check=True)
        # Ensure the .gitmodules file is updated
        subprocess.run(["git", "add", ".gitmodules"], check=True)
        subprocess.run(["git", "commit", "-m", f"Removed submodule {path}"], check=False)
        # Remove the metadata from .git/config
        subprocess.run(["git", "config", "--remove-section", f"submodule.{path}"], check=False)
        # Clean up leftover paths
        git_modules_path = os.path.join(".git", "modules", os.path.normpath(path))
        if os.path.exists(git_modules_path):
            shutil.rmtree(git_modules_path, ignore_errors=True)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        print(f"Successfully removed submodule: {path}")
    except Exception as e:
        print(f"Failed to remove submodule '{path}': {e}")

def main():
    """Main function to execute the script."""
    while True:
        choice = display_welcome()

        if choice == "1":
            scan_and_update_submodules()

        elif choice == "2":
            sync_existing_submodules()

        elif choice == "3":
            print("Exiting... Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
