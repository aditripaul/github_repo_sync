# ------------------------------------------------------------------------------
#
#  sync_github_repo.py
#
#  This script mirrors all repositories from a Github repositories to a local
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
from typing import Dict, Optional

import requests
from dotenv import load_dotenv


def list_repos(
    username: str,
    repo_type: str,
    token: Optional[str] = None,
    org_name: Optional[str] = None,
) -> Dict[str, str]:
    """
    Lists all repositories for a given GitHub individual user or organization.

    Args:
        username (str): The GitHub username.
        repo_type (str): The type of repositories to list (public, private, all).
        token (str, optional): The GitHub personal access token. Defaults to None.
        org_name (str, optional): The GitHub organization name. Defaults to None.

    Returns:
        dict: A dictionary containing repo name and clone url.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    headers["Accept"] = "application/vnd.github.v3+json"

    if org_name:
        url = f"https://api.github.com/orgs/{org_name}/repos?type={repo_type}"
        print(f"\n{repo_type.capitalize()} repositories for organization '{org_name}':")
    else:
        if token:
            url = f"https://api.github.com/user/repos?type={repo_type}"
        else:
            url = f"https://api.github.com/users/{username}/repos?type={repo_type}"
        print(f"\n{repo_type.capitalize()} repositories for user '{username}':")

    page = 1
    repo_dict = {}
    while True:
        try:
            response = requests.get(f"{url}&page={page}", headers=headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

            repos = response.json()
            if not repos:
                break  # No more repos, exit the loop

            for repo in repos:
                repo_dict[repo["name"]] = repo["clone_url"]
            page += 1
        except requests.exceptions.HTTPError as e:
            print(f"Error retrieving repositories: {e}")
            print(f"Response text: {response.text}")
            break
        except requests.exceptions.RequestException as e:
            print(f"A network error occurred: {e}")
            break
    return repo_dict


def mirror_repos(
    repos: Dict[str, str], folder: str, token: Optional[str] = None
) -> None:
    """
    Mirror clones the given repositories into the specified folder.
    If the repository already exists, it fetches all the changes.

    Args:
        repos (dict): A dictionary of repository names and their clone URLs.
        folder (str): The local folder to save the repositories.
        token (str, optional): The GitHub personal access token. Defaults to None.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    for repo_name, clone_url in repos.items():
        try:
            print(f"\nProcessing '{repo_name}'...")
            if token:
                clone_url = clone_url.replace("https://", f"https://{token}@")
            repo_path = os.path.join(folder, repo_name + ".git")

            if os.path.exists(repo_path):
                print(
                    f"Repository already exists. Fetching updates for '{repo_name}'..."
                )
                if token:
                    # Check if the remote URL needs to be updated with the token
                    remote_url = subprocess.check_output(
                        ["git", "config", "--get", "remote.origin.url"],
                        cwd=repo_path,
                        text=True,
                    ).strip()
                    if token not in remote_url:
                        print("Updating remote URL with token.")
                        subprocess.run(
                            ["git", "remote", "set-url", "origin", clone_url],
                            cwd=repo_path,
                            check=True,
                            text=True,
                        )
                subprocess.run(
                    [
                        "git",
                        "fetch",
                        "--all",
                        "--prune",
                        "--progress",
                    ],
                    cwd=repo_path,
                    check=True,
                    text=True,
                )
            else:
                print(f"Mirror cloning '{repo_name}' into '{repo_path}'...")
                subprocess.run(
                    ["git", "clone", "--mirror", "--progress", clone_url, repo_path],
                    check=True,
                    text=True,
                )
        except subprocess.CalledProcessError:
            print(
                f"  ERROR: Failed to process repository '{repo_name}'. Git command failed. See output above for details."
            )
        except FileNotFoundError:
            print(
                "  ERROR: 'git' command not found. Is Git installed and in your PATH?"
            )
            break  # Stop if git is not installed


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="List GitHub repositories for a user or organization."
    )
    parser.add_argument(
        "--username",
        default=os.getenv("GH_USERNAME"),
        help="The GitHub username.",
        type=str,
    )
    parser.add_argument(
        "--repo_type",
        choices=["public", "private", "all"],
        default="all",
        help="The type of repositories to list.",
        type=str,
    )
    parser.add_argument(
        "--org",
        default=os.getenv("GH_ORG"),
        help="The GitHub organization name (optional).",
        type=str,
    )
    parser.add_argument(
        "--folder",
        default="github_sync/git_repos",
        help="Local folder to save the repositories.",
        type=str,
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GH_TOKEN"),
        help="The GitHub personal access token. If not provided, it will look for GH_TOKEN in your environment variables or a .env file.",
        type=str,
    )
    parser.add_argument(
        "--user-only",
        action="store_true",
        help="Force syncing for the user, ignoring any GH_ORG set in the environment.",
    )

    args = parser.parse_args()

    # If --user-only is specified, ignore the organization from the environment
    # and sync for the user instead. This provides a convenient override.
    if args.user_only:
        args.org = None

    if not args.username:
        parser.error(
            "Username must be provided either as an argument or in the .env file as GH_USERNAME"
        )

    repos = list_repos(args.username, args.repo_type, args.token, args.org)

    if args.org:
        target_folder = f"{args.folder}_{args.org}"
    else:
        target_folder = f"{args.folder}_{args.username}"

    print(f"{len(repos)} github_repos found.")
    if repos:
        mirror_repos(repos, target_folder, args.token)

# example .env
# GH_USERNAME=username
# GH_ORG=organization
# GH_TOKEN=token
