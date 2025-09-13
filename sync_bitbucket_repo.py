# ------------------------------------------------------------------------------
#
#  sync_bitbucket_repo.py
#
#  This script mirrors all repositories from a Bitbucket workspace to a local
#  directory. It can authenticate using an Atlassian API token and can clone
#  repositories via HTTPS or SSH.
#
#  Author: Aditri Paul
#  License: GNU GPLv3
#
# ------------------------------------------------------------------------------

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, cast

import requests
from dotenv import load_dotenv

# Constants
BITBUCKET_API_URL = "https://api.bitbucket.org/2.0"


def list_bitbucket_repos(
    workspace: str,
    token: Optional[str] = None,
    user: Optional[str] = None,
    ssh: bool = False,
) -> Optional[Dict[str, str]]:
    """
    Lists all repositories for a given Bitbucket workspace.

    Args:
        workspace (str): The Bitbucket workspace (username or team name).
        token (str, optional): An Atlassian API token.
        user (str, optional): Your Atlassian account email (for API token auth).
        ssh (bool): If True, retrieve SSH clone URLs instead of HTTPS.

    Returns:
        A dictionary containing repo name and clone url, or None on failure.
    """
    headers = {}
    auth = None
    if user and token:
        auth = (user, token)
    elif token:
        # This case might be for OAuth tokens, but Atlassian API tokens are recommended
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BITBUCKET_API_URL}/repositories/{workspace}"
    print(f"\nListing repositories for workspace '{workspace}'...")

    clone_type = "ssh" if ssh else "https"
    repo_dict = {}
    while url:
        try:
            response = requests.get(url, headers=headers, auth=auth)
            response.raise_for_status()

            data = response.json()
            for repo in data.get("values", []):
                repo_name = repo["name"]
                clone_url = ""
                for clone_link in repo.get("links", {}).get("clone", []):
                    if clone_link.get("name") == clone_type:
                        clone_url = clone_link.get("href")
                        break
                if clone_url:
                    repo_dict[repo_name] = clone_url
                else:
                    print(
                        f"  Warning: No {clone_type} clone URL found for '{repo_name}'.",
                        file=sys.stderr,
                    )

            url = data.get("next")  # Get the URL for the next page

        except requests.exceptions.HTTPError as e:
            print(f"Error: Failed to retrieve repositories: {e}", file=sys.stderr)
            if e.response is not None:
                if e.response.status_code in [401, 403]:
                    print(
                        "  Authentication failed. Please check your credentials.",
                        file=sys.stderr,
                    )
                    print(
                        "  - Verify your BB_USER (Atlassian email) and BB_TOKEN (Atlassian API token).",
                        file=sys.stderr,
                    )
                print(f"  Response: {e.response.text}", file=sys.stderr)
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error: A network error occurred: {e}", file=sys.stderr)
            return None
    return repo_dict


def mirror_repos(
    repos: Dict[str, str],
    folder: str,
    token: Optional[str] = None,
    user: Optional[str] = None,
) -> None:
    """
    Mirror clones the given repositories into the specified folder.
    If the repository already exists, it fetches all the changes.

    Args:
        repos (dict): A dictionary of repository names and their clone URLs.
        folder (str): The local folder to save the repositories.
        token (str, optional): An Atlassian API token.
        user (str, optional): Your Atlassian account email (for API token auth).
    """
    base_path = Path(folder)
    try:
        base_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create directory {base_path}: {e}", file=sys.stderr)
        sys.exit(1)

    for repo_name, clone_url in repos.items():
        print(f"\nProcessing '{repo_name}'...")
        repo_path = base_path / f"{repo_name}.git"

        if clone_url.startswith("https://"):
            if user and token:
                # Atlassian API token authentication
                clone_url = clone_url.replace("https://", f"https://{user}:{token}@")

        try:
            if repo_path.exists():
                print(
                    f"Repository already exists. Fetching updates for '{repo_name}'..."
                )
                # Check if the remote URL needs to be updated with credentials
                try:
                    result = subprocess.run(
                        ["git", "config", "--get", "remote.origin.url"],
                        cwd=repo_path,
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    remote_url = result.stdout.strip()
                    if remote_url != clone_url:
                        print("Updating remote URL with credentials.")
                        subprocess.run(
                            ["git", "remote", "set-url", "origin", clone_url],
                            cwd=repo_path,
                            check=True,
                            capture_output=True,
                        )
                except subprocess.CalledProcessError as e:
                    print(
                        f"  Warning: Failed to check or update remote URL for '{repo_name}'.\n  {e.stderr}",
                        file=sys.stderr,
                    )
                subprocess.run(
                    ["git", "fetch", "--all", "--prune", "--progress"],
                    cwd=repo_path,
                    check=True,
                )
            else:
                print(f"Mirror cloning '{repo_name}' into '{repo_path}'...")
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--mirror",
                        "--progress",
                        clone_url,
                        str(repo_path),
                    ],
                    check=True,
                )
        except FileNotFoundError:
            print(
                "Error: 'git' command not found. Is Git installed and in your PATH?",
                file=sys.stderr,
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(
                f"  Error: Failed to process repository '{repo_name}'. Git command failed.",
                file=sys.stderr,
            )
            if e.stderr:
                print(f"  {e.stderr.strip()}", file=sys.stderr)


def main() -> None:
    """Main function to parse arguments and run the sync process."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Mirror Bitbucket repositories for a workspace."
    )
    parser.add_argument(
        "--workspace",
        default=os.getenv("BB_WORKSPACE"),
        help="The Bitbucket workspace (username or team name). Env: BB_WORKSPACE",
        type=str,
    )
    parser.add_argument(
        "--user",
        default=os.getenv("BB_USER"),
        help="Your Atlassian account email for authentication. Env: BB_USER",
        type=str,
    )
    parser.add_argument(
        "--token",
        default=os.getenv("BB_TOKEN"),
        help="An Atlassian API token for authentication. Env: BB_TOKEN",
        type=str,
    )
    parser.add_argument(
        "--folder",
        default="bitbucket_sync",
        help="Local base folder for backups. A subfolder will be created for the workspace.",
        type=str,
    )
    parser.add_argument(
        "--ssh",
        action="store_true",
        help="Use SSH clone URLs. Overrides BB_USE_SSH from .env.",
    )
    parser.add_argument(
        "--no-ssh",
        action="store_true",
        help="Do not use SSH clone URLs. Overrides BB_USE_SSH from .env.",
    )

    args = parser.parse_args()

    if args.ssh and args.no_ssh:
        parser.error("argument --ssh: not allowed with argument --no-ssh")

    # Determine whether to use SSH
    use_ssh_env = os.getenv("BB_USE_SSH", "false").lower() in ("true", "1", "yes")
    if args.ssh:
        ssh_flag = True
    elif args.no_ssh:
        ssh_flag = False
    else:
        ssh_flag = use_ssh_env

    if not args.workspace:
        parser.error(
            "Workspace must be provided via --workspace or BB_WORKSPACE in .env file"
        )

    repos = list_bitbucket_repos(args.workspace, args.token, args.user, ssh_flag)

    if repos is None:
        sys.exit(1)

    if not repos:
        print("No repositories found to mirror.")
        return

    target_folder = str(
        Path(args.folder) / cast(str, f"{args.folder}_{args.workspace}")
    )

    print(f"\nFound {len(repos)} repositories to sync.")
    print(f"Target directory: {target_folder}")

    mirror_repos(repos, target_folder, args.token, args.user)
    print("\nSync complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)

## example .env
# BB_WORKSPACE=workspace_name
# BB_USER=your_atlassian_email
# BB_TOKEN=atlassian_api_token
# BB_USE_SSH=true
