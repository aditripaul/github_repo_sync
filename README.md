# GitHub Repository Mirroring Script

This Python script allows you to create local mirror clones of your GitHub repositories. It can back up repositories from a personal account or an entire organization, including public, private, or all repositories.

The script is designed to be run periodically (e.g., via a cron job) to keep a local, up-to-date, bare-metal backup of your source code.

## Features

*   **Mirror Repositories**: Creates full, mirror clones using `git clone --mirror`.
*   **User & Organization Support**: Backs up repositories from a personal GitHub account or a GitHub organization.
*   **Efficient Updates**: If a repository is already mirrored, it efficiently fetches only the new changes (`git fetch --all --prune`).
*   **Flexible Configuration**: Uses a `.env` file and command-line arguments for easy configuration.
*   **Repository Filtering**: Choose to mirror `public`, `private`, or `all` repositories.

## Prerequisites

*   Python 3.7+
*   Git

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The script can be configured using a `.env` file or command-line arguments.

### 1. Environment Variables (`.env` file)

Create a file named `.env` in the root of the project directory and add your configuration details. This is the recommended approach for storing sensitive information like your access token.

```env
# .env file

# Your GitHub username
GH_USERNAME="your-github-username"

# A GitHub Personal Access Token (PAT) with 'repo' scope
GH_TOKEN="ghp_yoursupersecrettoken"

# (Optional) The name of the organization you want to back up
GH_ORG="your-github-organization"
```

#### Creating a Personal Access Token (PAT)

You'll need a GitHub Personal Access Token to access private repositories or to avoid rate-limiting on the GitHub API.

For the best security, it is recommended to use a **Fine-grained personal access token**.

1.  Go to your GitHub **Settings** > **Developer settings** > **Personal access tokens** > **Fine-grained tokens**.
2.  Click **Generate new token**.
3.  Give the token a descriptive name and set an expiration date.
4.  Under **Repository access**, select **All repositories** to allow the script to back up everything, or select specific repositories if you prefer.
5.  Under **Permissions**, go to **Repository permissions**.
6.  Set the following permissions:
    *   **Contents**: `Read-only`. This is required to clone and fetch repository data.
    *   **Metadata**: `Read-only`. This is required to list the repositories.
7.  Click **Generate token** and copy it. **You will not be able to see it again.**

If you only need to mirror public repositories, you can create a token with access only to public repositories, which is more restrictive and secure.

### 2. Command-Line Arguments

You can override the `.env` configuration or provide all settings directly on the command line.

Run the script with `--help` to see all available options:

```bash
python sync_github_repo.py --help
```

#### Available aguments:
* --username: The GitHub username.
* --repo_type ["public", "private", "all"]:The type of repositories to list.
* --org: The GitHub organization name.
* --folder: The local folder to save the repositories.
* --token: The GitHub personal access token.
* --user-only: Force syncing for the user, ignoring any GH_ORG set in the environment.

## Usage

Once configured, you can run the script from your terminal. The mirrored repositories will be saved as bare `.git` directories in a folder like `github_sync/git_repos_<username>` or `github_sync/git_repos_<orgname>`.

### Examples

**1. Mirror all repositories for the user defined in `.env`:**

```bash
python sync_github_repo.py
```

**2. Mirror all repositories for a specific organization:**

(This assumes `GH_USERNAME` and `GH_TOKEN` are set in your `.env` file for authentication).
```bash
python sync_github_repo.py --org my-cool-org
```

**3. Mirror only public repositories for a user, specifying all details via arguments:**

```bash
python sync_github_repo.py --username some-user --repo_type public
```

**4. Mirror private repositories for a user into a custom folder:**

```bash
python sync_github_repo.py --username your-username --token "ghp_yourtoken" --repo_type private --folder /mnt/backups/github
```

## Security Note

For interacting with private repositories, this script embeds your Personal Access Token into the git remote URL (`https://<token>@github.com/...`). This may cause the token to be stored in plaintext within the `.git/config` file of each mirrored repository. Ensure that the machine and the directory where you run this script are secure.

## Disclaimer

This script is provided "as is" and without any warranty. The authors and contributors are not responsible for any data loss or other damages that may occur from using this software. You are solely responsible for verifying your backups and ensuring they are complete and restorable.

## License

This project is open-source and available under the GNU GPLv3 License.
