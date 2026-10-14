"""Main entry point for reddit-stock-trends."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .extractor import TickerExtractor, ExtractionResult
from .fetcher import RedditFetcher, RedditPost, SUBREDDITS


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Track stock ticker mentions in Reddit investing communities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--subreddits",
        nargs="+",
        default=SUBREDDITS,
        help=f"Subreddits to scan (default: {', '.join(SUBREDDITS)})",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=100,
        help="Number of posts to fetch per subreddit (default: 100)",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["hot", "new", "top"],
        default="hot",
        help="Post sorting mode (default: hot)",
    )
    parser.add_argument(
        "-t",
        "--time-filter",
        choices=["hour", "day", "week", "month", "year", "all"],
        default="day",
        help="Time filter for top posts (default: day)",
    )
    parser.add_argument(
        "-n",
        "--top-n",
        type=int,
        default=20,
        help="Number of top tickers to display (default: 20)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (JSON format)",
    )
    parser.add_argument(
        "--include-comments",
        action="store_true",
        help="Also scan comments (slower)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Only match known valid tickers (default: True)",
    )
    parser.add_argument(
        "--no-strict",
        action="store_false",
        dest="strict",
        help="Match any potential ticker pattern",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    return parser.parse_args()


def fetch_posts(
    fetcher: RedditFetcher,
    subreddits: list[str],
    mode: str,
    limit: int,
    time_filter: str,
    verbose: bool,
) -> list[RedditPost]:
    """Fetch posts based on mode."""
    posts = []
    if verbose:
        print(f"Fetching {mode} posts from: {', '.join(subreddits)}")

    if mode == "hot":
        posts = list(fetcher.fetch_hot_posts(subreddits, limit))
    elif mode == "new":
        posts = list(fetcher.fetch_new_posts(subreddits, limit))
    elif mode == "top":
        posts = list(fetcher.fetch_top_posts(subreddits, limit, time_filter))

    if verbose:
        print(f"Fetched {len(posts)} posts")
    return posts


def extract_tickers_from_posts(
    posts: list[RedditPost],
    extractor: TickerExtractor,
    verbose: bool,
) -> ExtractionResult:
    """Extract tickers from posts."""
    result = ExtractionResult()
    for post in posts:
        text = f"{post.title} {post.selftext}"
        post_result = extractor.extract_from_text(text)
        result.merge(post_result)

    if verbose:
        print(f"Found {result.total_mentions} ticker mentions")
    return result


def format_output(
    result: ExtractionResult,
    top_n: int,
    subreddits: list[str],
    mode: str,
) -> dict:
    """Format extraction results as a dictionary."""
    top_tickers = result.top_tickers(top_n)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subreddits": subreddits,
        "mode": mode,
        "total_mentions": result.total_mentions,
        "unique_tickers": len(result.tickers),
        "top_tickers": [
            {
                "ticker": t.ticker,
                "mentions": t.count,
                "sample_contexts": t.contexts[:3],
            }
            for t in top_tickers
        ],
    }


def print_results(output: dict, top_n: int) -> None:
    """Print results to console."""
    print("\n" + "=" * 60)
    print("REDDIT STOCK TRENDS")
    print("=" * 60)
    print(f"Timestamp: {output['timestamp']}")
    print(f"Subreddits: {', '.join(output['subreddits'])}")
    print(f"Mode: {output['mode']}")
    print(f"Total mentions: {output['total_mentions']}")
    print(f"Unique tickers: {output['unique_tickers']}")
    print("\n" + "-" * 60)
    print(f"TOP {top_n} MENTIONED TICKERS")
    print("-" * 60)

    for i, ticker_data in enumerate(output["top_tickers"], 1):
        print(f"{i:3}. ${ticker_data['ticker']:5} - {ticker_data['mentions']} mentions")

    print("=" * 60 + "\n")


def main() -> int:
    """Main entry point."""
    load_dotenv()
    args = parse_args()

    try:
        fetcher = RedditFetcher()
        extractor = TickerExtractor(strict_mode=args.strict)

        posts = fetch_posts(
            fetcher=fetcher,
            subreddits=args.subreddits,
            mode=args.mode,
            limit=args.limit,
            time_filter=args.time_filter,
            verbose=args.verbose,
        )

        result = extract_tickers_from_posts(
            posts=posts,
            extractor=extractor,
            verbose=args.verbose,
        )

        output = format_output(
            result=result,
            top_n=args.top_n,
            subreddits=args.subreddits,
            mode=args.mode,
        )

        print_results(output, args.top_n)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            if args.verbose:
                print(f"Results saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
