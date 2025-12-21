"""
Sentiment Analysis Service
Analyzes sentiment based on:
1. Live price data from NASDAQ (primary)
2. News text using OpenAI GPT-4o-mini (secondary)
"""

from typing import Dict, Optional
import os
import aiohttp
import json


class SentimentService:
    def __init__(self):
        """Initialize sentiment analysis with OpenAI"""
        self.api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o-mini"

        if self.api_key == "YOUR_OPENAI_API_KEY_HERE":
            print("WARNING: OpenAI API key not set. Add OPENAI_API_KEY to environment variables.")
            print("   Get your key at: https://platform.openai.com/api-keys")
        else:
            print(f"SUCCESS: Sentiment analysis using OpenAI {self.model}")

    async def analyze_text(self, text: str) -> Dict:
        """Analyze sentiment of text using OpenAI GPT-4o-mini"""
        if not text or len(text.strip()) == 0:
            return {
                "score": 0,
                "label": "neutral",
                "confidence": 0,
                "summary": "No text to analyze"
            }

        if self.api_key == "YOUR_OPENAI_API_KEY_HERE":
            print("OpenAI API key not configured, using keyword fallback")
            return await self._analyze_with_keywords(text)

        try:
            return await self._analyze_with_openai(text)
        except Exception as e:
            print(f"Error in OpenAI sentiment analysis: {e}")
            return await self._analyze_with_keywords(text)

    async def _analyze_with_openai(self, text: str) -> Dict:
        """Analyze sentiment using OpenAI GPT-4o-mini"""
        try:
            # Truncate text if too long
            text_truncated = text[:1000] if len(text) > 1000 else text

            prompt = f"""Analyze the sentiment of the following financial news/text.
Provide your response in this exact JSON format:
{{
    "label": "positive" or "negative" or "neutral",
    "score": a number between -1 and 1 (negative to positive),
    "confidence": a number between 0 and 1,
    "reasoning": "brief explanation"
}}

Text to analyze:
{text_truncated}"""

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a financial sentiment analysis expert. Analyze text and return sentiment scores in JSON format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200
                }

                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"OpenAI API error: {response.status} - {error_text}")
                        return await self._analyze_with_keywords(text)

                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]

                    # Parse JSON response
                    # Try to extract JSON from markdown code blocks if present
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()

                    result = json.loads(content)

                    return {
                        "score": round(float(result.get("score", 0)), 3),
                        "label": result.get("label", "neutral"),
                        "confidence": round(float(result.get("confidence", 0.5)), 3),
                        "summary": f"Sentiment: {result.get('label', 'neutral').upper()} - {result.get('reasoning', 'OpenAI analysis')}"
                    }

        except Exception as e:
            print(f"Error parsing OpenAI response: {e}")
            return await self._analyze_with_keywords(text)

    async def _analyze_with_keywords(self, text: str) -> Dict:
        """Fallback: Analyze sentiment using keyword matching"""
        text_lower = text.lower()

        # Financial sentiment keywords
        positive_words = [
            "up", "rise", "gain", "surge", "growth", "profit", "success",
            "rally", "soar", "bull", "bullish", "record", "beat", "exceed",
            "strong", "positive", "upgrade", "boost", "high", "improve",
            "outperform", "buy", "optimistic", "recover"
        ]

        negative_words = [
            "down", "fall", "drop", "decline", "loss", "fail", "concern",
            "plunge", "crash", "bear", "bearish", "miss", "below", "weak",
            "negative", "downgrade", "cut", "low", "worsen", "underperform",
            "sell", "pessimistic", "risk", "slump"
        ]

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        total = pos_count + neg_count
        score = (pos_count - neg_count) / total if total > 0 else 0

        # Normalize score to -1 to 1
        score = max(-1, min(1, score))

        label = "neutral"
        if score > 0.15:
            label = "positive"
        elif score < -0.15:
            label = "negative"

        confidence = abs(score) if total > 0 else 0.1

        return {
            "score": round(score, 3),
            "label": label,
            "confidence": round(confidence, 3),
            "summary": f"Sentiment: {label.upper()} (keyword-based)"
        }

    def analyze_price_sentiment(self, price_data: Dict) -> Dict:
        """
        Analyze sentiment based on live price data from NASDAQ
        This is the PRIMARY sentiment indicator - price action tells the real story

        Args:
            price_data: NASDAQ price data with pctChange, volume, etc.

        Returns:
            Sentiment dict with score, label, confidence
        """
        try:
            # Extract percentage change (e.g., "+3.93%" -> 3.93)
            pct_change_str = price_data.get('pctChange', '0%')
            pct_change = float(pct_change_str.replace('%', '').replace('+', ''))

            # Extract volume (e.g., "324,925,927" -> 324925927)
            volume_str = price_data.get('volume', '0')
            volume = int(volume_str.replace(',', ''))

            # Calculate sentiment score based on percentage change
            # Score ranges from -1 (very negative) to +1 (very positive)
            if pct_change >= 5.0:
                score = 1.0
                label = "very_positive"
                summary = f"Strong rally: +{pct_change}%"
            elif pct_change >= 2.0:
                score = 0.7
                label = "positive"
                summary = f"Good gains: +{pct_change}%"
            elif pct_change >= 0.5:
                score = 0.4
                label = "slightly_positive"
                summary = f"Modest gains: +{pct_change}%"
            elif pct_change > -0.5:
                score = 0.0
                label = "neutral"
                summary = f"Flat: {pct_change:+.2f}%"
            elif pct_change > -2.0:
                score = -0.4
                label = "slightly_negative"
                summary = f"Modest decline: {pct_change}%"
            elif pct_change > -5.0:
                score = -0.7
                label = "negative"
                summary = f"Notable drop: {pct_change}%"
            else:
                score = -1.0
                label = "very_negative"
                summary = f"Sharp selloff: {pct_change}%"

            # Calculate confidence based on volume
            # Higher volume = higher confidence in the sentiment
            # Average volume threshold: 50M shares (adjust based on typical volumes)
            volume_confidence = min(volume / 100_000_000, 1.0)  # Cap at 1.0
            confidence = max(0.5, volume_confidence)  # Minimum 50% confidence

            return {
                "score": round(score, 3),
                "label": label,
                "confidence": round(confidence, 3),
                "summary": summary,
                "source": "price_action",
                "pct_change": pct_change,
                "volume": volume
            }

        except Exception as e:
            print(f"Error analyzing price sentiment: {e}")
            return {
                "score": 0.0,
                "label": "neutral",
                "confidence": 0.1,
                "summary": "Unable to analyze price data",
                "source": "error"
            }

    async def analyze_combined_sentiment(
        self,
        symbol: str,
        price_data: Optional[Dict] = None,
        news_text: Optional[str] = None,
        price_weight: float = 0.7,
        news_weight: float = 0.3
    ) -> Dict:
        """
        Combined sentiment analysis: Price (70%) + News (30%)

        Args:
            symbol: Stock symbol
            price_data: NASDAQ price data (optional)
            news_text: News text to analyze (optional)
            price_weight: Weight for price sentiment (default 70%)
            news_weight: Weight for news sentiment (default 30%)

        Returns:
            Combined sentiment with breakdown
        """
        price_sentiment = None
        news_sentiment = None

        # Analyze price sentiment (primary)
        if price_data:
            price_sentiment = self.analyze_price_sentiment(price_data)

        # Analyze news sentiment (secondary)
        if news_text:
            news_sentiment = await self.analyze_text(news_text)

        # If only price data available, use 100% price-based sentiment
        if price_sentiment and not news_sentiment:
            return {
                **price_sentiment,
                "method": "price_only",
                "breakdown": {
                    "price": price_sentiment
                }
            }

        # If only news available, use 100% news-based sentiment
        if news_sentiment and not price_sentiment:
            return {
                **news_sentiment,
                "method": "news_only",
                "breakdown": {
                    "news": news_sentiment
                }
            }

        # Combine both (weighted average)
        if price_sentiment and news_sentiment:
            combined_score = (
                price_sentiment["score"] * price_weight +
                news_sentiment["score"] * news_weight
            )

            combined_confidence = (
                price_sentiment["confidence"] * price_weight +
                news_sentiment["confidence"] * news_weight
            )

            # Determine final label
            if combined_score >= 0.6:
                label = "very_positive"
            elif combined_score >= 0.3:
                label = "positive"
            elif combined_score >= 0.1:
                label = "slightly_positive"
            elif combined_score > -0.1:
                label = "neutral"
            elif combined_score > -0.3:
                label = "slightly_negative"
            elif combined_score > -0.6:
                label = "negative"
            else:
                label = "very_negative"

            return {
                "score": round(combined_score, 3),
                "label": label,
                "confidence": round(combined_confidence, 3),
                "summary": f"{price_sentiment['summary']} | News: {news_sentiment['label']}",
                "method": "combined",
                "breakdown": {
                    "price": price_sentiment,
                    "news": news_sentiment,
                    "weights": {
                        "price": price_weight,
                        "news": news_weight
                    }
                }
            }

        # Fallback
        return {
            "score": 0.0,
            "label": "neutral",
            "confidence": 0.1,
            "summary": "No data available for sentiment analysis",
            "method": "none"
        }
