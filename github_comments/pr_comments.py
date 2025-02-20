import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


@dataclass
class Comment:
    author: str
    body: str
    created_at: str
    url: str
    commit_id: Optional[str] = None
    commit_message: Optional[str] = None

    @property
    def formatted_date(self) -> str:
        dt = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

    @property
    def short_commit_id(self) -> Optional[str]:
        return self.commit_id[:7] if self.commit_id else None


class GitHubPRCommentsClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.endpoint = "https://api.github.com/graphql"

    def execute_query(self, query: str, variables: dict) -> dict:
        response = requests.post(
            self.endpoint,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        response.raise_for_status()
        json_response = response.json()

        return json_response

    def get_pr_comments(self, owner: str, repo: str, pr_number: int, filter_type: str = 'unresolved') -> List[Comment]:
        query = """
        query($owner: String!, $name: String!, $pull_number: Int!, $review_after: String) {
          repository(owner: $owner, name: $name) {
            pullRequest(number: $pull_number) {
              comments(first: 100) {
                nodes {
                  body
                  createdAt
                  author {
                    login
                  }
                  url
                }
                pageInfo {
                  endCursor
                  hasNextPage
                }
              }
              reviewThreads(first: 100, after: $review_after) {
                nodes {
                  isResolved
                  comments(first: 100) {
                    nodes {
                      body
                      createdAt
                      author {
                        login
                      }
                      url
                      originalCommit {
                        oid
                        message
                        author {
                          name
                          email
                        }
                      }
                    }
                  }
                }
                pageInfo {
                  endCursor
                  hasNextPage
                }
              }
            }
          }
        }
        """

        all_comments = []
        review_cursor = None

        while True:
            variables = {
                "owner": owner,
                "name": repo,
                "pull_number": pr_number,
                "review_after": review_cursor
            }

            data = self.execute_query(query, variables)
            pr_data = data["data"]["repository"]["pullRequest"]

            page_comments = self._parse_response(pr_data, filter_type)
            all_comments.extend(page_comments)

            review_page_info = pr_data["reviewThreads"]["pageInfo"]
            review_cursor = review_page_info["endCursor"] if review_page_info["hasNextPage"] else None

            if not review_cursor:
                break

        return all_comments

    def _parse_response(self, pr_data: dict, filter_type: str = 'unresolved') -> List[Comment]:
        comments = []

        threads = pr_data["reviewThreads"]["nodes"]
        for thread in threads:
            if filter_type == 'unresolved' and thread["isResolved"]:
                continue

            for comment in thread["comments"]["nodes"]:
                commit_data = comment.get("originalCommit", {})

                comments.append(Comment(
                    author=comment["author"]["login"] if comment["author"] else "unknown",
                    body=comment["body"],
                    created_at=comment["createdAt"],
                    url=comment["url"],
                    commit_id=commit_data.get("oid"),
                    commit_message=commit_data.get("message")
                ))

        return comments


class CommentsDisplay:
    def __init__(self):
        self.console = Console()

    def display_comments(self, comments: List[Comment]):
        if not comments:
            self.console.print(Panel("No unresolved comments found",
                                     style="yellow"))
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("Author", style="green")
        table.add_column("Commit", style="yellow", width=60)
        table.add_column("Comment", style="white")
        table.add_column("URL", style="blue")

        for comment in comments:
            if comment.commit_id:
                commit_msg = comment.commit_message.split('\n')[0] if comment.commit_message else 'No commit message'
                commit_info = f"{comment.short_commit_id}\n{commit_msg}"
            else:
                commit_info = "N/A"

            table.add_row(
                comment.formatted_date,
                comment.author,
                commit_info,
                Text(comment.body, overflow="fold"),
                comment.url
            )

        self.console.print(table)
        filter_type = "unresolved" if len(comments) == 1 else "total"
        self.console.print(f"\n[bold green]Total {filter_type} comments:[/] {len(comments)}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and display unresolved GitHub PR comments"
    )
    parser.add_argument(
        "--owner",
        default="zeronetworks",
        help="Repository owner (default: %(default)s)"
    )
    parser.add_argument(
        "--repo",
        default="zero-core",
        help="Repository name (default: %(default)s)"
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=5875,
        help="Pull request number (default: %(default)s)"
    )
    parser.add_argument(
        "--filter",
        choices=['all', 'unresolved'],
        default='unresolved',
        help="Filter comments (default: %(default)s)"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    github_token = os.environ.get("GH_TOKEN")
    if not github_token:
        raise ValueError(
            "GH_TOKEN environment variable not set. "
            "Please set it with your GitHub Personal Access Token."
        )

    try:
        client = GitHubPRCommentsClient(github_token)
        display = CommentsDisplay()

        comments = client.get_pr_comments(args.owner, args.repo, args.pr, args.filter)
        display.display_comments(comments)

    except requests.exceptions.RequestException as e:
        Console().print(f"[bold red]Error making request to GitHub:[/] {str(e)}")
    except Exception as e:
        Console().print(f"[bold red]An error occurred:[/] {str(e)}")


if __name__ == "__main__":
    main()
