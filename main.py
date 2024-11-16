import os
import subprocess
import requests
import shutil
import json
from tqdm import tqdm  # For progress bar
from submodule_functions import scan_existing_submodule_paths, remove_submodule, sync_submodules

GITHUB_CONFIG_FILE = "config.json"
SUBMODULE_DIRECTORY = "submodules"

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

    toggle_repo_selection(repos, existing_repos)

def toggle_repo_selection(repos, existing_repos):
    """Display and allow toggling of repository selection."""
    existing_repos_set = {os.path.basename(repo) for repo in existing_repos}  # Compare by directory name
    repo_status = {
        repo['name']: (repo['name'] in existing_repos_set)
        for repo in repos
    }

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
            os.makedirs(SUBMODULE_DIRECTORY, exist_ok=True)
            updated_submodules = []

            for repo in tqdm(repos, desc="Processing repositories"):
                repo_path = os.path.normpath(os.path.join(SUBMODULE_DIRECTORY, repo['name']))
                if repo_status[repo['name']]:
                    try:
                        if not os.path.exists(repo_path):
                            subprocess.run(["git", "submodule", "add", "-b", "main", repo['clone_url'], repo_path], check=True)
                        else:
                            subprocess.run(["git", "submodule", "update", "--init", "--remote", repo_path], check=True)
                    except subprocess.CalledProcessError as e:
                        tqdm.write(f"Failed to add or update submodule '{repo['name']}': {e.stderr or str(e)}")
                else:
                    try:
                        remove_submodule(repo_path)
                    except Exception as e:
                        tqdm.write(f"Failed to remove submodule '{repo['name']}': {str(e)}")

                if repo_status[repo['name']]:
                    updated_submodules.append({
                        "directory": repo['name'],
                        "url": repo['clone_url'],
                        "branch": "main"
                    })
                clear_screen()

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
    """Update all existing submodules and remove untracked ones."""
    print("Syncing all existing submodules...")
    try:
        # Get the list of existing submodules from Git
        existing_submodules = scan_existing_submodule_paths()

        # Get the desired submodules from .gitmodules
        desired_submodules = {}
        result = subprocess.run(["git", "config", "--file", ".gitmodules", "--get-regexp", "path"], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                key, path = line.split(maxsplit=1)
                submodule_name = key.split(".")[1]  # Extract submodule name
                desired_submodules[os.path.normpath(path)] = submodule_name

        for submodule_path in tqdm(existing_submodules, desc="Syncing submodules"):
            submodule_name = os.path.basename(submodule_path)  # Use directory name
            if submodule_path in desired_submodules:
                try:
                    subprocess.run(
                        ["git", "submodule", "update", "--init", "--remote", submodule_path],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    tqdm.write(f"Failed to update submodule '{submodule_name}': {e.stderr or str(e)}")
            else:
                tqdm.write(f"Submodule '{submodule_name}' not listed in .gitmodules. Removing...")
                try:
                    remove_submodule(submodule_path)
                except Exception as e:
                    tqdm.write(f"Failed to remove submodule '{submodule_name}': {e}")

        print("All submodules are up to date.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to sync submodules: {e.stderr or str(e)}")

def main():
    """Main function to execute the script."""
    while True:
        choice = display_welcome()

        if choice == "1":
            scan_and_update_submodules()
            input("Press Enter to continue...")

        elif choice == "2":
            sync_existing_submodules()
            input("Press Enter to continue...")

        elif choice == "3":
            print("Exiting... Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
