# Repository Mirroring Scripts

This project contains Python scripts to create local mirror clones of GitHub and Bitbucket repositories.

---

## GitHub Repository Mirroring

This Python script allows for creating local mirror clones of GitHub repositories. It can back up repositories from a personal account or an entire organization, including public, private, or all repositories.

The script is designed to be run periodically (e.g., via a cron job) to keep a local, up-to-date, bare-metal backup of the source code.

### Features

*   **Mirror Repositories**: Creates full, mirror clones using `git clone --mirror`.
*   **User & Organization Support**: Backs up repositories from a personal GitHub account or a GitHub organization.
*   **Efficient Updates**: If a repository is already mirrored, it efficiently fetches only new changes (`git fetch --all --prune`).
*   **Flexible Configuration**: Uses a `.env` file and command-line arguments for easy configuration.
*   **Repository Filtering**: Choose to mirror `public`, `private`, or `all` repositories.

### Prerequisites

*   Python 3.7+
*   Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/example-user/repo-name.git
    cd repo-name
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

The script can be configured using a `.env` file or command-line arguments.

#### 1. Environment Variables (`.env` file)

A `.env` file can be created in the root of the project directory to add configuration details. This is the recommended approach for storing sensitive information like an access token.

```env
# .env file

# The GitHub username
GH_USERNAME="github-username"

# A GitHub Personal Access Token (PAT) with 'repo' scope
GH_TOKEN="ghp_supersecrettoken"

# (Optional) The name of the organization to back up
GH_ORG="github-organization"
```

#### Creating a Personal Access Token (PAT)

A GitHub Personal Access Token is needed to access private repositories or to avoid rate-limiting on the GitHub API.

For the best security, it is recommended to use a **Fine-grained personal access token**.

1.  Navigate to GitHub **Settings** > **Developer settings** > **Personal access tokens** > **Fine-grained tokens**.
2.  Click **Generate new token**.
3.  Give the token a descriptive name and set an expiration date.
4.  Under **Repository access**, select **All repositories** to allow the script to back up everything, or select specific repositories.
5.  Under **Permissions**, go to **Repository permissions**.
6.  Set the following permissions:
    *   **Contents**: `Read-only`. This is required to clone and fetch repository data.
    *   **Metadata**: `Read-only`. This is required to list the repositories.
7.  Click **Generate token** and copy it. The token will not be shown again.

If only public repositories need to be mirrored, a token with access only to public repositories can be created, which is more restrictive and secure.

#### 2. Command-Line Arguments

The `.env` configuration can be overridden by providing settings directly on the command line.

Run the script with `--help` to see all available options:

```bash
python sync_github_repo.py --help
```

Available aguments:
* --username: The GitHub username.
* --repo_type ["public", "private", "all"]:The type of repositories to list.
* --org: The GitHub organization name.
* --folder: The local folder to save the repositories.
* --token: The GitHub personal access token.
* --user-only: Force syncing for the user, ignoring any GH_ORG set in the environment.

### Usage

Once configured, the script can be run from the terminal. The mirrored repositories will be saved as bare `.git` directories in a folder like `github_sync/git_repos_<username>` or `github_sync/git_repos_<orgname>`.

#### Examples

**1. Mirror all repositories for the user defined in `.env`:**

```bash
python sync_github_repo.py
```

**2. Mirror all repositories for a specific organization:**

(This assumes `GH_USERNAME` and `GH_TOKEN` are set in the `.env` file for authentication).
```bash
python sync_github_repo.py --org my-cool-org
```

**3. Mirror only public repositories for a user, specifying all details via arguments:**

```bash
python sync_github_repo.py --username some-user --repo_type public
```

**4. Mirror private repositories for a user into a custom folder:**

```bash
python sync_github_repo.py --username github-username --token "ghp_token" --repo_type private --folder /mnt/backups/github
```

---

## Bitbucket Repository Mirroring

This Python script allows for creating local mirror clones of Bitbucket repositories for a given workspace.

### Features

*   **Mirror Repositories**: Creates full, mirror clones using `git clone --mirror`.
*   **Efficient Updates**: If a repository is already mirrored, it efficiently fetches only new changes (`git fetch --all --prune`).
*   **Flexible Configuration**: Uses a `.env` file and command-line arguments for easy configuration.
*   **Authentication**: Supports authentication using an Atlassian account email and an Atlassian API token.
*   **SSH & HTTPS**: Can use either SSH or HTTPS clone URLs.

### Configuration

The script can be configured using a `.env` file or command-line arguments.

#### 1. Environment Variables (`.env` file)

The `.env` file should be created or edited in the root of the project directory.

```env
# .env file for Bitbucket

# The Bitbucket workspace (username or team name)
BB_WORKSPACE="bitbucket-workspace"

# The Atlassian account email
BB_USER="email@example.com"

# An Atlassian API Token
BB_TOKEN="atlassian_api_token"

# --- To use SSH by default ---
# Set to 'true' to use SSH clone URLs by default
BB_USE_SSH=true
```

#### Creating an Atlassian API Token

The API token will have the same access as the Atlassian account. Ensure the account has read access to the repositories to be mirrored.

1.  Log in to the Atlassian account at: https://id.atlassian.com/manage-profile/security/api-tokens.
2.  Click on "Create API token".
3.  Give the token a descriptive name (e.g., "bitbucket-sync-script").
4.  Click "Create".
5.  Click "Copy to clipboard" and save the token. The token will not be shown again.

#### 2. Command-Line Arguments

Run the script with `--help` to see all available options:

```bash
python sync_bitbucket_repo.py --help
```

Available arguments:
* `--workspace`: The Bitbucket workspace.
* `--user`: The Atlassian account email.
* `--token`: The Atlassian API token.
* `--folder`: The local folder to save the repositories.
* `--ssh`: Use SSH clone URLs.
* `--no-ssh`: Do not use SSH clone URLs.

### Usage

Mirrored repositories will be saved as bare `.git` directories in a folder like `bitbucket_sync/<workspace>`.

#### Examples

**1. Mirror all repositories for a workspace using credentials from `.env`:**

```bash
python sync_bitbucket_repo.py
```

**2. Mirror all repositories using command-line arguments:**

```bash
python sync_bitbucket_repo.py --workspace my-workspace --user email@example.com --token "atlassian_api_token"
```

**3. Mirror all repositories using SSH clone URLs:**

(This assumes SSH keys are configured in Bitbucket.)
```bash
python sync_bitbucket_repo.py --workspace my-workspace --ssh
```

## Security Note

For interacting with private repositories, this script embeds the Personal Access Token into the git remote URL (`https://<token>@github.com/...`). This may cause the token to be stored in plaintext within the `.git/config` file of each mirrored repository. The machine and the directory where this script is run should be secure.

## Disclaimer

This script is provided "as is" and without any warranty. The authors and contributors are not responsible for any data loss or other damages that may occur from using this software. Verifying backups for completeness and restorability is the user's responsibility.

## License

This project is open-source and available under the GNU GPLv3 License.