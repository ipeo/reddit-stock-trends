"""Extractor module for identifying stock tickers and topics in text."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


DATA_DIR = Path(__file__).parent / "data"


def load_tickers(filepath: Path | None = None) -> set[str]:
    """Load valid stock tickers from a file.

    Args:
        filepath: Path to tickers file. Defaults to data/tickers.txt.

    Returns:
        Set of valid ticker symbols (uppercase).
    """
    filepath = filepath or DATA_DIR / "tickers.txt"
    if not filepath.exists():
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip()}


def load_stopwords(filepath: Path | None = None) -> set[str]:
    """Load stopwords to filter out common words that look like tickers.

    Args:
        filepath: Path to stopwords file. Defaults to data/stopwords.txt.

    Returns:
        Set of stopwords (uppercase).
    """
    filepath = filepath or DATA_DIR / "stopwords.txt"
    if not filepath.exists():
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip()}


@dataclass
class TickerMention:
    """Represents a ticker mention with context."""

    ticker: str
    count: int
    contexts: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Result of ticker extraction from text."""

    tickers: dict[str, TickerMention] = field(default_factory=dict)
    total_mentions: int = 0

    def add_mention(self, ticker: str, context: str = "") -> None:
        """Add a ticker mention."""
        ticker = ticker.upper()
        if ticker not in self.tickers:
            self.tickers[ticker] = TickerMention(ticker=ticker, count=0)
        self.tickers[ticker].count += 1
        if context:
            self.tickers[ticker].contexts.append(context[:200])
        self.total_mentions += 1

    def top_tickers(self, n: int = 10) -> list[TickerMention]:
        """Get the top N most mentioned tickers."""
        sorted_tickers = sorted(
            self.tickers.values(), key=lambda x: x.count, reverse=True
        )
        return sorted_tickers[:n]

    def merge(self, other: "ExtractionResult") -> "ExtractionResult":
        """Merge another extraction result into this one."""
        for ticker, mention in other.tickers.items():
            if ticker not in self.tickers:
                self.tickers[ticker] = TickerMention(ticker=ticker, count=0)
            self.tickers[ticker].count += mention.count
            self.tickers[ticker].contexts.extend(mention.contexts)
        self.total_mentions += other.total_mentions
        return self


class TickerExtractor:
    """Extracts stock ticker mentions from text."""

    TICKER_PATTERN = re.compile(
        r"(?<![a-zA-Z])"
        r"\$?([A-Z]{1,5})"
        r"(?![a-zA-Z])"
    )

    CASHTAG_PATTERN = re.compile(r"\$([A-Z]{1,5})(?![a-zA-Z])")

    def __init__(
        self,
        valid_tickers: set[str] | None = None,
        stopwords: set[str] | None = None,
        strict_mode: bool = True,
    ) -> None:
        """Initialize the ticker extractor.

        Args:
            valid_tickers: Set of valid ticker symbols. Loaded from file if None.
            stopwords: Set of words to exclude. Loaded from file if None.
            strict_mode: If True, only match tickers in valid_tickers set.
        """
        self.valid_tickers = valid_tickers if valid_tickers is not None else load_tickers()
        self.stopwords = stopwords if stopwords is not None else load_stopwords()
        self.strict_mode = strict_mode

    def is_valid_ticker(self, ticker: str) -> bool:
        """Check if a string is a valid ticker symbol.

        Args:
            ticker: Potential ticker symbol.

        Returns:
            True if valid, False otherwise.
        """
        ticker = ticker.upper()
        if ticker in self.stopwords:
            return False
        if self.strict_mode and self.valid_tickers:
            return ticker in self.valid_tickers
        return len(ticker) >= 1 and len(ticker) <= 5

    def extract_from_text(self, text: str) -> ExtractionResult:
        """Extract ticker mentions from a single text.

        Args:
            text: Text to extract tickers from.

        Returns:
            ExtractionResult with found tickers.
        """
        result = ExtractionResult()

        cashtag_matches = list(self.CASHTAG_PATTERN.finditer(text.upper()))
        cashtag_positions = set()
        for match in cashtag_matches:
            ticker = match.group(1)
            if self.is_valid_ticker(ticker):
                context = self._get_context(text, ticker)
                result.add_mention(ticker, context)
                cashtag_positions.add(match.start())

        for match in re.finditer(r"\b([A-Z]{1,5})\b", text):
            word = match.group(1)
            if self.is_valid_ticker(word):
                start_in_upper = match.start()
                if start_in_upper - 1 not in cashtag_positions:
                    context = self._get_context(text, word)
                    result.add_mention(word, context)

        return result

    def extract_from_texts(self, texts: Iterable[str]) -> ExtractionResult:
        """Extract ticker mentions from multiple texts.

        Args:
            texts: Iterable of texts to extract from.

        Returns:
            Combined ExtractionResult.
        """
        combined = ExtractionResult()
        for text in texts:
            result = self.extract_from_text(text)
            combined.merge(result)
        return combined

    def _get_context(self, text: str, ticker: str, window: int = 50) -> str:
        """Get surrounding context for a ticker mention.

        Args:
            text: Full text.
            ticker: Ticker symbol to find context for.
            window: Number of characters before/after to include.

        Returns:
            Context string.
        """
        pattern = re.compile(
            rf"(?i)(.{{0,{window}}}\$?{re.escape(ticker)}.{{0,{window}}})"
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return ""


def count_ticker_mentions(
    texts: Iterable[str],
    valid_tickers: set[str] | None = None,
    stopwords: set[str] | None = None,
) -> Counter:
    """Simple function to count ticker mentions across texts.

    Args:
        texts: Iterable of texts to analyze.
        valid_tickers: Set of valid tickers. Loaded from file if None.
        stopwords: Set of stopwords. Loaded from file if None.

    Returns:
        Counter of ticker mentions.
    """
    extractor = TickerExtractor(
        valid_tickers=valid_tickers,
        stopwords=stopwords,
        strict_mode=bool(valid_tickers),
    )
    result = extractor.extract_from_texts(texts)
    return Counter({t.ticker: t.count for t in result.tickers.values()})
