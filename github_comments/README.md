# GitHub PR Comments Fetcher

A script to fetch and display pull request comments from GitHub, linking each comment to its respective commit.

## Usage

```sh
GH_TOKEN=your_github_token python3 pr_comments.py --owner zeronetworks --repo zero-on-prem --pr 52
```

## Requirements

- Python 3.9+
- GitHub Personal Access Token (`GH_TOKEN`)

## Features

- Fetches PR comments and review threads
- Displays comments linked to their respective commits
- Supports unresolved comment filtering
