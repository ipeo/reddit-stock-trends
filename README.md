# reddit-stock-trends

Track stock ticker and topic mentions across Reddit investing communities.

A read-only Python tool that uses [PRAW](https://praw.readthedocs.io/) (Python Reddit API Wrapper) to analyze posts from popular investing subreddits and identify trending stock tickers.

## Features

- **Multi-subreddit scanning**: Monitors r/stocks, r/investing, r/wallstreetbets, r/StockMarket, r/options, and r/CanadianInvestor
- **Flexible sorting**: Fetch hot, new, or top posts with configurable time filters
- **Ticker extraction**: Identifies stock symbols via cashtags ($AAPL) and uppercase mentions (AAPL)
- **Stopword filtering**: Filters out common words that look like tickers (CEO, DD, ATH, etc.)
- **Validated tickers**: Optional strict mode matches only known valid ticker symbols
- **Context capture**: Stores surrounding text for each mention
- **JSON output**: Export results for further analysis

## Installation

### Prerequisites

- Python 3.9+
- Reddit API credentials ([create an app](https://www.reddit.com/prefs/apps))

### Install from source

```bash
git clone https://github.com/boninpo/market-sentiment.git
cd market-sentiment
pip install -e .
```

### Install dependencies only

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` with your Reddit API credentials:

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=reddit-stock-trends/0.1.0 (by /u/your_username)
```

### Getting Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Select "script" as the application type
4. Fill in the name and description
5. Set redirect URI to `http://localhost:8080`
6. Click "create app"
7. Copy the client ID (under the app name) and client secret

## Usage

### Command Line

```bash
# Basic usage - fetch hot posts from default subreddits
reddit-stock-trends

# Fetch new posts with higher limit
reddit-stock-trends --mode new --limit 200

# Fetch top posts from the past week
reddit-stock-trends --mode top --time-filter week

# Scan specific subreddits
reddit-stock-trends -s wallstreetbets stocks

# Save results to JSON
reddit-stock-trends -o results.json

# Show top 50 tickers
reddit-stock-trends --top-n 50

# Verbose mode
reddit-stock-trends -v
```

### Python API

```python
from reddit_stock_trends.fetcher import RedditFetcher
from reddit_stock_trends.extractor import TickerExtractor

# Initialize fetcher and extractor
fetcher = RedditFetcher()
extractor = TickerExtractor(strict_mode=True)

# Fetch posts
posts = list(fetcher.fetch_hot_posts(limit=50))

# Extract tickers
for post in posts:
    text = f"{post.title} {post.selftext}"
    result = extractor.extract_from_text(text)
    for ticker, mention in result.tickers.items():
        print(f"{ticker}: {mention.count} mentions")
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--subreddits` | `-s` | Subreddits to scan |
| `--limit` | `-l` | Posts per subreddit (default: 100) |
| `--mode` | `-m` | Sort mode: hot, new, top (default: hot) |
| `--time-filter` | `-t` | Time filter for top: hour, day, week, month, year, all |
| `--top-n` | `-n` | Number of top tickers to display (default: 20) |
| `--output` | `-o` | Output JSON file path |
| `--strict` | | Only match known valid tickers (default) |
| `--no-strict` | | Match any potential ticker pattern |
| `--include-comments` | | Also scan post comments (slower) |
| `--verbose` | `-v` | Verbose output |

## Project Structure

```
market-sentiment/
├── src/
│   └── reddit_stock_trends/
│       ├── __init__.py
│       ├── main.py          # CLI entry point
│       ├── fetcher.py       # Reddit API integration
│       ├── extractor.py     # Ticker extraction logic
│       └── data/
│           ├── tickers.txt  # Valid ticker symbols
│           └── stopwords.txt # Words to filter out
├── tests/
│   └── test_extractor.py    # Unit tests
├── .env.example             # Example environment config
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Monitored Subreddits

| Subreddit | Description |
|-----------|-------------|
| r/stocks | General stock market discussion |
| r/investing | Long-term investing strategies |
| r/wallstreetbets | High-risk trading and memes |
| r/StockMarket | Market news and analysis |
| r/options | Options trading discussion |
| r/CanadianInvestor | Canadian market focus |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=reddit_stock_trends
```

### Code Structure

- **fetcher.py**: Handles Reddit API calls via PRAW. Provides `RedditPost` and `RedditComment` dataclasses and `RedditFetcher` class for fetching content.
- **extractor.py**: Contains `TickerExtractor` class that identifies ticker symbols using regex patterns, validates against known tickers, and filters stopwords.
- **main.py**: CLI entry point that orchestrates fetching and extraction, formats output, and handles JSON export.

## Sample Output

```
============================================================
REDDIT STOCK TRENDS
============================================================
Timestamp: 2024-01-15T10:30:00+00:00
Subreddits: stocks, investing, wallstreetbets, StockMarket, options, CanadianInvestor
Mode: hot
Total mentions: 1247
Unique tickers: 156

------------------------------------------------------------
TOP 20 MENTIONED TICKERS
------------------------------------------------------------
  1. $NVDA  - 89 mentions
  2. $TSLA  - 76 mentions
  3. $AAPL  - 65 mentions
  4. $SPY   - 54 mentions
  5. $AMD   - 48 mentions
  ...
============================================================
```

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool is for informational purposes only. It does not constitute financial advice. Always do your own research before making investment decisions.
