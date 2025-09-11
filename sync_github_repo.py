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
        response = requests.get(f"{url}&page={page}", headers=headers)
        if response.status_code == 200:
            repos = response.json()
            if not repos:
                break
            for repo in repos:
                repo_dict[repo["name"]] = repo["clone_url"]
            page += 1
        else:
            print(
                f"Error: Could not retrieve repositories. Status code: {response.status_code}"
            )
            print(response.json())
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
        print(f"Cloning {repo_name}...")
        if token:
            clone_url = clone_url.replace("https://", f"https://{token}@")
        repo_path = os.path.join(folder, repo_name + ".git")
        if os.path.exists(repo_path):
            print(f"Repository {repo_name} already exists. Fetching updates...")
            if token:
                remote_url = subprocess.check_output(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd=repo_path,
                ).decode()
                if token not in remote_url:
                    subprocess.run(
                        [
                            "git",
                            "remote",
                            "set-url",
                            "origin",
                            clone_url,
                        ],
                        cwd=repo_path,
                    )
            subprocess.run(["git", "fetch", "--all"], cwd=repo_path)
        else:
            print(f"Mirror cloning {repo_name} into {repo_path}...")
            subprocess.run(["git", "clone", "--mirror", clone_url, repo_path])
        break


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
        default="git_repos",
        help="Local folder to save the repositories.",
        type=str,
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GH_TOKEN"),
        help="The GitHub personal access token. If not provided, it will look for GH_TOKEN in your environment variables or a .env file.",
        type=str,
    )

    args = parser.parse_args()

    if not args.username:
        parser.error(
            "Username must be provided either as an argument or in the .env file as GH_USERNAME"
        )

    repos = list_repos(args.username, args.repo_type, args.token, args.org)
    # print(repos)

    if args.org:
        args.folder = f"{args.folder}_{args.org}"
    else:
        args.folder = f"{args.folder}_{args.username}"

    print(f"{len(repos)} github_repos found.")
    if repos:
        mirror_repos(repos, args.folder, args.token)

# example .env
# GH_USERNAME=username
# GH_ORG=organization
# GH_TOKEN=token
