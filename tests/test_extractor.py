"""Tests for the extractor module."""

import pytest

from reddit_stock_trends.extractor import (
    TickerExtractor,
    ExtractionResult,
    TickerMention,
    count_ticker_mentions,
    load_tickers,
    load_stopwords,
)


class TestTickerMention:
    """Tests for TickerMention dataclass."""

    def test_creation(self):
        mention = TickerMention(ticker="AAPL", count=5)
        assert mention.ticker == "AAPL"
        assert mention.count == 5
        assert mention.contexts == []

    def test_creation_with_contexts(self):
        mention = TickerMention(ticker="TSLA", count=3, contexts=["context1", "context2"])
        assert mention.ticker == "TSLA"
        assert mention.count == 3
        assert len(mention.contexts) == 2


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_empty_result(self):
        result = ExtractionResult()
        assert result.tickers == {}
        assert result.total_mentions == 0

    def test_add_mention(self):
        result = ExtractionResult()
        result.add_mention("AAPL", "I love AAPL")
        assert "AAPL" in result.tickers
        assert result.tickers["AAPL"].count == 1
        assert result.total_mentions == 1

    def test_add_multiple_mentions_same_ticker(self):
        result = ExtractionResult()
        result.add_mention("AAPL", "context1")
        result.add_mention("AAPL", "context2")
        assert result.tickers["AAPL"].count == 2
        assert result.total_mentions == 2

    def test_add_mentions_different_tickers(self):
        result = ExtractionResult()
        result.add_mention("AAPL")
        result.add_mention("TSLA")
        assert len(result.tickers) == 2
        assert result.total_mentions == 2

    def test_top_tickers(self):
        result = ExtractionResult()
        for _ in range(10):
            result.add_mention("AAPL")
        for _ in range(5):
            result.add_mention("TSLA")
        for _ in range(3):
            result.add_mention("MSFT")

        top = result.top_tickers(2)
        assert len(top) == 2
        assert top[0].ticker == "AAPL"
        assert top[0].count == 10
        assert top[1].ticker == "TSLA"
        assert top[1].count == 5

    def test_merge(self):
        result1 = ExtractionResult()
        result1.add_mention("AAPL")
        result1.add_mention("TSLA")

        result2 = ExtractionResult()
        result2.add_mention("AAPL")
        result2.add_mention("MSFT")

        result1.merge(result2)
        assert result1.tickers["AAPL"].count == 2
        assert result1.tickers["TSLA"].count == 1
        assert result1.tickers["MSFT"].count == 1
        assert result1.total_mentions == 4


class TestTickerExtractor:
    """Tests for TickerExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor with known tickers and stopwords."""
        valid_tickers = {"AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "GME", "AMC", "NVDA"}
        stopwords = {"I", "A", "THE", "CEO", "DD", "IMO", "ATH"}
        return TickerExtractor(
            valid_tickers=valid_tickers,
            stopwords=stopwords,
            strict_mode=True,
        )

    @pytest.fixture
    def non_strict_extractor(self):
        """Create an extractor without strict mode."""
        stopwords = {"I", "A", "THE", "CEO", "DD", "IMO", "ATH"}
        return TickerExtractor(
            valid_tickers=None,
            stopwords=stopwords,
            strict_mode=False,
        )

    def test_is_valid_ticker_strict(self, extractor):
        assert extractor.is_valid_ticker("AAPL") is True
        assert extractor.is_valid_ticker("aapl") is True
        assert extractor.is_valid_ticker("TSLA") is True
        assert extractor.is_valid_ticker("INVALID") is False

    def test_is_valid_ticker_stopword(self, extractor):
        assert extractor.is_valid_ticker("CEO") is False
        assert extractor.is_valid_ticker("DD") is False
        assert extractor.is_valid_ticker("IMO") is False

    def test_extract_cashtag(self, extractor):
        text = "I just bought $AAPL and $TSLA"
        result = extractor.extract_from_text(text)
        assert "AAPL" in result.tickers
        assert "TSLA" in result.tickers
        assert result.total_mentions == 2

    def test_extract_uppercase(self, extractor):
        text = "AAPL is going up! Also watching TSLA"
        result = extractor.extract_from_text(text)
        assert "AAPL" in result.tickers
        assert "TSLA" in result.tickers

    def test_extract_mixed(self, extractor):
        text = "Buying $AAPL and also looking at TSLA and MSFT"
        result = extractor.extract_from_text(text)
        assert len(result.tickers) == 3

    def test_extract_multiple_occurrences(self, extractor):
        text = "$AAPL is great. I also bought more AAPL yesterday."
        result = extractor.extract_from_text(text)
        assert result.tickers["AAPL"].count == 2

    def test_cashtag_and_uppercase_both_counted(self, extractor):
        text = "$AAPL AAPL"
        result = extractor.extract_from_text(text)
        assert result.tickers["AAPL"].count == 2

    def test_extract_ignores_stopwords(self, extractor):
        text = "THE CEO said I think DD shows ATH"
        result = extractor.extract_from_text(text)
        assert "THE" not in result.tickers
        assert "CEO" not in result.tickers
        assert "DD" not in result.tickers

    def test_extract_ignores_invalid_tickers(self, extractor):
        text = "NOTREAL ticker and FAKE symbol"
        result = extractor.extract_from_text(text)
        assert "NOTREAL" not in result.tickers
        assert "FAKE" not in result.tickers

    def test_extract_from_texts(self, extractor):
        texts = [
            "I love $AAPL",
            "TSLA to the moon!",
            "$AAPL and $MSFT are great",
        ]
        result = extractor.extract_from_texts(texts)
        assert result.tickers["AAPL"].count == 2
        assert result.tickers["TSLA"].count == 1
        assert result.tickers["MSFT"].count == 1

    def test_extract_context(self, extractor):
        text = "I think AAPL will go up because of the new iPhone"
        result = extractor.extract_from_text(text)
        assert len(result.tickers["AAPL"].contexts) > 0
        assert "AAPL" in result.tickers["AAPL"].contexts[0]

    def test_non_strict_mode(self, non_strict_extractor):
        text = "Looking at NEWT and ZZZZ tickers"
        result = non_strict_extractor.extract_from_text(text)
        assert "NEWT" in result.tickers
        assert "ZZZZ" in result.tickers

    def test_empty_text(self, extractor):
        result = extractor.extract_from_text("")
        assert result.total_mentions == 0

    def test_no_tickers_text(self, extractor):
        text = "This is just regular text without any stock symbols"
        result = extractor.extract_from_text(text)
        assert result.total_mentions == 0


class TestCountTickerMentions:
    """Tests for count_ticker_mentions function."""

    def test_basic_count(self):
        texts = ["$AAPL is great", "TSLA to the moon", "$AAPL again"]
        valid_tickers = {"AAPL", "TSLA"}
        counts = count_ticker_mentions(texts, valid_tickers=valid_tickers)
        assert counts["AAPL"] == 2
        assert counts["TSLA"] == 1

    def test_empty_texts(self):
        counts = count_ticker_mentions([])
        assert len(counts) == 0


class TestLoadFunctions:
    """Tests for file loading functions."""

    def test_load_tickers_default(self):
        tickers = load_tickers()
        assert isinstance(tickers, set)
        if tickers:
            assert all(t.isupper() for t in tickers)

    def test_load_stopwords_default(self):
        stopwords = load_stopwords()
        assert isinstance(stopwords, set)
        if stopwords:
            assert all(s.isupper() for s in stopwords)
