import os
import subprocess
import shutil
import stat

SUBMODULE_DIRECTORY = "submodules"

def get_existing_submodules():
    """Get the list of currently registered submodules."""
    result = subprocess.run(["git", "submodule"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching existing submodules: {result.stderr}")
        return {}

    submodules = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            submodules[parts[1]] = parts[0]
    return submodules

def scan_existing_submodule_paths():
    """Scan the submodule directory for existing submodule paths."""
    submodule_paths = []
    submodule_dir = os.path.join('.', SUBMODULE_DIRECTORY)
    if os.path.exists(submodule_dir):
        for folder in os.listdir(submodule_dir):
            full_path = os.path.join(submodule_dir, folder)
            if os.path.isdir(full_path):
                git_folder = os.path.join(full_path, ".git")
                if os.path.exists(git_folder):
                    submodule_paths.append(folder)
    return submodule_paths

def add_or_update_submodule(path, url, branch="main"):
    """Add or update a submodule."""
    if not os.path.exists(path):
        print(f"Adding submodule: {path}")
        try:
            subprocess.run(["git", "submodule", "add", "-b", branch, url, path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to add submodule '{path}': {e.stderr or str(e)}")
    else:
        print(f"Updating submodule: {path}")
        try:
            subprocess.run(["git", "submodule", "update", "--remote", "--merge", path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to update submodule '{path}': {e.stderr or str(e)}")

def remove_readonly(func, path, exc_info):
    """Handle readonly files during shutil.rmtree."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def remove_submodule(path):
    """Remove a submodule and update .gitmodules."""
    print(f"Attempting to remove submodule: {path}")
    try:
        # Deinitialize the submodule
        subprocess.run(["git", "submodule", "deinit", "-f", path], check=True)
        # Remove the submodule from the .gitmodules file
        subprocess.run(["git", "rm", "-f", path], check=True)
        # Remove the metadata from .git/config
        subprocess.run(["git", "config", "--remove-section", f"submodule.{path}"], check=False)
        # Clean up leftover paths
        git_modules_path = os.path.join(".git", "modules", path)
        if os.path.exists(git_modules_path):
            shutil.rmtree(git_modules_path, ignore_errors=True)
        print(f"Successfully removed submodule: {path}")
    except Exception as e:
        print(f"Failed to remove submodule '{path}': {e}")

def remove_submodule(path):
    """Remove a submodule and update .gitmodules."""
    print(f"Attempting to remove submodule: {path}")
    try:
        # Deinitialize the submodule
        subprocess.run(["git", "submodule", "deinit", "-f", path], check=True)
        # Remove the submodule from the repository
        subprocess.run(["git", "rm", "-rf", path], check=True)
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

def remove_submodule_duplicate(path):
    """Remove a submodule and update .gitmodules."""
    print(f"Attempting to remove submodule: {path}")
    try:
        # Deinitialize the submodule
        subprocess.run(["git", "submodule", "deinit", "-f", path], check=True)
        # Remove the submodule from the repository
        subprocess.run(["git", "rm", "-f", path], check=True)
        # Remove the metadata from .git/config
        subprocess.run(["git", "config", "--remove-section", f"submodule.{path}"], check=False)
        # Clean up leftover paths
        git_modules_path = os.path.join(".git", "modules", path)
        if os.path.exists(git_modules_path):
            shutil.rmtree(git_modules_path, ignore_errors=True)
        print(f"Successfully removed submodule: {path}")
    except Exception as e:
        print(f"Failed to remove submodule '{path}': {e}")

def remove_submodule_old (path):
    """Remove a submodule."""
    print(f"Attempting to remove submodule: {path}")
    try:
        # Deinitialize the submodule if it's registered
        deinit_result = subprocess.run(["git", "submodule", "deinit", "-f", path], capture_output=True, text=True)
        if deinit_result.returncode != 0:
            print(f"Warning: Could not deinitialize submodule '{path}': {deinit_result.stderr.strip()}")
        
        # Remove the submodule directory
        if os.path.exists(path):
            print(f"Removing directory for submodule: {path}")
            shutil.rmtree(path, onerror=remove_readonly)
        else:
            print(f"Directory '{path}' does not exist, skipping.")

        # Remove submodule metadata in .git/modules
        git_modules_path = os.path.join(".git", "modules", path)
        if os.path.exists(git_modules_path):
            print(f"Removing .git/modules for submodule: {path}")
            shutil.rmtree(git_modules_path, onerror=remove_readonly)
        else:
            print(f".git/modules path '{git_modules_path}' does not exist, skipping.")
    except Exception as e:
        print(f"Failed to remove submodule '{path}': {str(e)}")

def sync_submodules(config):
    """Sync submodules based on the configuration."""
    print("Syncing submodules...")
    existing_submodules = get_existing_submodules()
    scanned_paths = scan_existing_submodule_paths()

    # Add or update submodules
    for submodule in config.get("submodules", []):
        path = submodule.get("path")
        url = submodule.get("url")
        branch = submodule.get("branch", "main")

        if not path or not url:
            print("Invalid submodule entry in configuration file.")
            continue

        add_or_update_submodule(path, url, branch)
        existing_submodules.pop(path, None)
        if path in scanned_paths:
            scanned_paths.remove(path)

    # Remove submodules not in the configuration
    for path in existing_submodules.keys():
        print(f"Submodule '{path}' not listed in config. Removing...")
        remove_submodule(path)

    # Remove submodules that exist in the folder but are not listed in the configuration
    for path in scanned_paths:
        print(f"Untracked submodule directory '{path}' found. Removing...")
        remove_submodule(path)

