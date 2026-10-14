"""Fetcher module for retrieving Reddit posts and comments using PRAW."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterator

import praw
from praw.models import Submission, Comment


SUBREDDITS = [
    "stocks",
    "investing",
    "wallstreetbets",
    "StockMarket",
    "options",
    "CanadianInvestor",
]


@dataclass
class RedditPost:
    """Represents a Reddit post with relevant metadata."""

    id: str
    subreddit: str
    title: str
    selftext: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    author: str | None

    @classmethod
    def from_submission(cls, submission: Submission) -> "RedditPost":
        """Create a RedditPost from a PRAW Submission object."""
        return cls(
            id=submission.id,
            subreddit=submission.subreddit.display_name,
            title=submission.title,
            selftext=submission.selftext or "",
            score=submission.score,
            num_comments=submission.num_comments,
            created_utc=submission.created_utc,
            url=submission.url,
            author=str(submission.author) if submission.author else None,
        )


@dataclass
class RedditComment:
    """Represents a Reddit comment with relevant metadata."""

    id: str
    subreddit: str
    body: str
    score: int
    created_utc: float
    author: str | None
    parent_id: str

    @classmethod
    def from_comment(cls, comment: Comment, subreddit: str) -> "RedditComment":
        """Create a RedditComment from a PRAW Comment object."""
        return cls(
            id=comment.id,
            subreddit=subreddit,
            body=comment.body or "",
            score=comment.score,
            created_utc=comment.created_utc,
            author=str(comment.author) if comment.author else None,
            parent_id=comment.parent_id,
        )


class RedditFetcher:
    """Fetches posts and comments from Reddit investing communities."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize the Reddit fetcher with API credentials.

        Args:
            client_id: Reddit API client ID. Defaults to REDDIT_CLIENT_ID env var.
            client_secret: Reddit API client secret. Defaults to REDDIT_CLIENT_SECRET env var.
            user_agent: User agent string. Defaults to REDDIT_USER_AGENT env var.
        """
        self.reddit = praw.Reddit(
            client_id=client_id or os.getenv("REDDIT_CLIENT_ID"),
            client_secret=client_secret or os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=user_agent
            or os.getenv("REDDIT_USER_AGENT", "reddit-stock-trends/0.1.0"),
        )

    def fetch_hot_posts(
        self,
        subreddits: list[str] | None = None,
        limit: int = 100,
    ) -> Iterator[RedditPost]:
        """Fetch hot posts from specified subreddits.

        Args:
            subreddits: List of subreddit names. Defaults to SUBREDDITS.
            limit: Maximum number of posts per subreddit.

        Yields:
            RedditPost objects.
        """
        subreddits = subreddits or SUBREDDITS
        for subreddit_name in subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            for submission in subreddit.hot(limit=limit):
                yield RedditPost.from_submission(submission)

    def fetch_new_posts(
        self,
        subreddits: list[str] | None = None,
        limit: int = 100,
    ) -> Iterator[RedditPost]:
        """Fetch newest posts from specified subreddits.

        Args:
            subreddits: List of subreddit names. Defaults to SUBREDDITS.
            limit: Maximum number of posts per subreddit.

        Yields:
            RedditPost objects.
        """
        subreddits = subreddits or SUBREDDITS
        for subreddit_name in subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            for submission in subreddit.new(limit=limit):
                yield RedditPost.from_submission(submission)

    def fetch_top_posts(
        self,
        subreddits: list[str] | None = None,
        limit: int = 100,
        time_filter: str = "day",
    ) -> Iterator[RedditPost]:
        """Fetch top posts from specified subreddits.

        Args:
            subreddits: List of subreddit names. Defaults to SUBREDDITS.
            limit: Maximum number of posts per subreddit.
            time_filter: Time filter (hour, day, week, month, year, all).

        Yields:
            RedditPost objects.
        """
        subreddits = subreddits or SUBREDDITS
        for subreddit_name in subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            for submission in subreddit.top(time_filter=time_filter, limit=limit):
                yield RedditPost.from_submission(submission)

    def fetch_comments(
        self,
        post: RedditPost,
        limit: int | None = None,
    ) -> Iterator[RedditComment]:
        """Fetch comments from a specific post.

        Args:
            post: The RedditPost to fetch comments from.
            limit: Maximum number of comments. None for all.

        Yields:
            RedditComment objects.
        """
        submission = self.reddit.submission(id=post.id)
        submission.comments.replace_more(limit=limit)
        for comment in submission.comments.list():
            yield RedditComment.from_comment(comment, post.subreddit)
