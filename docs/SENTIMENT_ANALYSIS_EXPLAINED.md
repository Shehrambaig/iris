# How Sentiment Analysis & News Fetching Works

## Overview

The system has **two main components**:
1. **News Fetching** - Gets news articles from the internet
2. **Sentiment Analysis** - Analyzes if news is positive, negative, or neutral

---

## 📰 How News is Fetched

### Flow Diagram:
```
Price Movement Detected (>0.5% change)
    ↓
SentimentAgent.monitorPriceMovement()
    ↓
fetchNewsWithSentiment(symbol)
    ↓
Frontend calls: GET /api/news/{symbol}
    ↓
Backend fetches from:
    1. Yahoo Finance (yfinance library) - PRIMARY
    2. NewsAPI.org (optional, needs API key)
    3. Other sources (scraping, RSS feeds)
    ↓
Returns news articles with timestamps
```

### Step-by-Step:

1. **Trigger**: When price moves >0.5%, the `SentimentAgent` is triggered
2. **News Fetch**: Agent calls `fetchNewsWithSentiment(symbol, 20)` to get 20 recent articles
3. **Backend Call**: Frontend makes HTTP request to `GET /api/news/NVDA?limit=20`
4. **Backend Processing** (in `backend-example.py`):
   ```python
   ticker = yf.Ticker(symbol)  # yfinance library
   news = ticker.news[:limit]   # Gets news from Yahoo Finance
   ```
5. **Response**: Backend returns JSON with:
   - Title, content, source, published date, URL
   - Each article is tagged with the stock symbol

### News Sources:

**Primary: Yahoo Finance (yfinance)**
- ✅ Free, no API key needed
- ✅ Built into yfinance library
- ✅ Gets news directly from Yahoo Finance
- ✅ Includes title, summary, publisher, timestamp

**Optional: NewsAPI.org**
- Requires free API key
- More comprehensive news sources
- Better filtering options
- Update `backend-example.py` with your API key

**Alternative Sources:**
- Alpha Vantage news endpoint
- Financial news RSS feeds
- Web scraping (BeautifulSoup)

---

## 🧠 How Sentiment Analysis Works

### Two Methods:

### Method 1: Advanced (Backend with AI Model) - **RECOMMENDED**

**Flow:**
```
News Article Text
    ↓
Frontend: POST /api/sentiment/analyze {text: "..."}
    ↓
Backend: Uses Hugging Face Transformers
    ↓
Model: cardiffnlp/twitter-roberta-base-sentiment-latest
    ↓
Returns: {score: -0.8, label: "negative", confidence: 0.95}
```

**How it works:**
1. Backend uses **Hugging Face Transformers** library
2. Uses pre-trained model: `cardiffnlp/twitter-roberta-base-sentiment-latest`
3. This is a **RoBERTa model** trained on Twitter data for sentiment
4. Model analyzes the text and returns:
   - **Score**: -1 (very negative) to +1 (very positive)
   - **Label**: "positive", "negative", or "neutral"
   - **Confidence**: How sure the model is (0 to 1)

**Example:**
```python
# Backend code (backend-example.py)
from transformers import pipeline

sentiment_pipeline = pipeline("sentiment-analysis", 
    model="cardiffnlp/twitter-roberta-base-sentiment-latest")
result = sentiment_pipeline("Nvidia stock surges 5% after strong earnings")

# Returns: {
#   "label": "LABEL_2",  # positive
#   "score": 0.95        # 95% confident
# }
```

### Method 2: Basic (Client-Side Fallback)

**If backend is unavailable**, frontend uses simple keyword matching:

**Flow:**
```
News Article Text
    ↓
performBasicSentimentAnalysis(text)
    ↓
Count positive words: "up", "rise", "gain", "surge", "growth", "profit"
Count negative words: "down", "fall", "drop", "decline", "loss", "fail"
    ↓
Calculate: score = (positiveCount - negativeCount) / total
    ↓
Return: {score: 0.6, label: "positive", confidence: 0.6}
```

**How it works:**
1. Converts text to lowercase
2. Counts occurrences of positive/negative keywords
3. Calculates score: `(positive - negative) / total`
4. Labels as positive if score > 0.2, negative if < -0.2, else neutral

**Example:**
```javascript
Text: "Nvidia stock rises after strong earnings report"
Positive words found: "rises", "strong" = 2
Negative words found: 0
Score: (2 - 0) / 2 = 1.0 (very positive)
Label: "positive"
```

---

## 🔄 Complete Flow: Price Event → News → Sentiment

### Example Scenario:

**1. Price Movement Detected:**
```
NVDA price: $177.00 → $179.50 (1.4% increase)
    ↓
SentimentAgent detects: changePercent = 1.4% > 0.5% threshold
    ↓
Triggers: analyzePriceEvent()
```

**2. Fetch Related News:**
```javascript
// In SentimentAgent
const news = await fetchNewsWithSentiment('NVDA', 20);
// Gets 20 most recent NVDA news articles
```

**3. Filter by Time Window:**
```javascript
// Only news from last 2 hours
const timeWindow = 2 * 3600 * 1000; // 2 hours
const relevantNews = news.filter(article => {
  const articleTime = new Date(article.publishedAt).getTime();
  return Math.abs(articleTime - timestamp) < timeWindow;
});
```

**4. Analyze Each Article:**
```javascript
// For each news article:
const sentiment = await analyzeSentiment(article.content);

// Example results:
Article 1: "Nvidia announces new AI chip" 
  → {score: 0.8, label: "positive", confidence: 0.9}

Article 2: "Nvidia faces supply chain issues"
  → {score: -0.6, label: "negative", confidence: 0.85}
```

**5. Calculate Overall Sentiment Impact:**
```javascript
// Average all sentiment scores
averageSentiment = (0.8 + (-0.6) + 0.3 + ...) / newsCount
// = 0.4 (slightly positive)

dominantSentiment = "positive" (since average > 0.2)
```

**6. Correlate with Price:**
```javascript
// Check if sentiment matches price movement
Price went UP (+1.4%)
News sentiment is POSITIVE (0.4)
→ Strong correlation! News likely caused the price increase
```

**7. Store Event:**
```javascript
const priceEvent = {
  timestamp: Date.now(),
  price: 179.50,
  change: +2.50,
  changePercent: +1.4%,
  correlatedNews: [article1, article2, ...],
  sentimentImpact: {
    averageSentiment: 0.4,
    dominantSentiment: "positive",
    newsCount: 5
  }
}
```

---

## 🎯 Key Features

### 1. **Automatic Triggering**
- Agent monitors price every second
- Only analyzes when price moves >0.5% (configurable)
- Saves resources by not analyzing every tiny movement

### 2. **Caching**
- News is cached per hour to avoid duplicate API calls
- Old cache entries (>24 hours) are automatically cleaned

### 3. **Time Correlation**
- Matches news timestamps with price movement times
- Uses 2-hour window to find relevant news
- Only considers news published around the price event

### 4. **Multiple Sentiment Methods**
- **Advanced**: AI model (if backend available)
- **Basic**: Keyword matching (fallback)
- Automatically chooses best available method

### 5. **Price Correlation**
- Calculates if news sentiment matches price direction
- Positive news + price increase = strong correlation
- Negative news + price decrease = strong correlation

---

## 📊 Data Structure

### NewsArticle:
```typescript
{
  id: "unique-id",
  title: "Nvidia stock surges after earnings",
  content: "Full article text...",
  source: "Reuters",
  publishedAt: "2025-01-12T10:30:00Z",
  url: "https://...",
  symbol: "NVDA",
  sentiment: {
    score: 0.8,        // -1 to 1
    label: "positive", // positive/negative/neutral
    confidence: 0.9,   // 0 to 1
    keywords: ["surge", "earnings"],
    summary: "Sentiment: positive (confidence: 0.9)"
  },
  priceAtTime: 179.50  // Price when news was published
}
```

### PriceEvent:
```typescript
{
  timestamp: 1705060800000,
  price: 179.50,
  change: 2.50,
  changePercent: 1.4,
  correlatedNews: [NewsArticle, ...],
  sentimentImpact: {
    averageSentiment: 0.4,
    dominantSentiment: "positive",
    newsCount: 5
  }
}
```

---

## 🔧 Configuration

### Adjust Sensitivity:
```typescript
// In sentimentAgent.ts, line 131
if (changePercent > 0.5) {  // Change this threshold
  // Analyze price event
}
```

### Adjust Time Window:
```typescript
// In sentimentAgent.ts, line 41
const timeWindow = 2 * 3600 * 1000;  // 2 hours, change as needed
```

### Change News Source:
Edit `backend-example.py`:
- Use NewsAPI.org (requires API key)
- Use Alpha Vantage
- Add web scraping
- Combine multiple sources

---

## 🚀 Current Implementation Status

✅ **News Fetching**: Working via Yahoo Finance (yfinance)  
✅ **Sentiment Analysis**: Basic keyword matching (fallback)  
⏳ **Advanced Sentiment**: Requires backend with transformers library  
✅ **Price Correlation**: Working  
✅ **Event Detection**: Working (>0.5% threshold)  
✅ **Caching**: Working (1-hour cache)  

---

## Next Steps to Enable Full Features

1. **Install backend dependencies:**
   ```bash
   pip install transformers torch
   ```

2. **Run backend:**
   ```bash
   python backend-example.py
   ```

3. **Optional: Get NewsAPI key:**
   - Sign up at newsapi.org (free tier available)
   - Update `backend-example.py` with your key
   - Better news coverage

4. **The system will automatically:**
   - Use AI sentiment analysis when backend is available
   - Fall back to keyword matching if backend is down
   - Fetch news from Yahoo Finance (always works)
   - Correlate news with price movements

---

## Example Output

When price moves, you'll see in console/logs:
```
Price Event Detected:
  Symbol: NVDA
  Price Change: +1.4% ($177.00 → $179.50)
  Time: 2025-01-12 10:30:00
  
Correlated News (5 articles found):
  1. "Nvidia announces new AI chip" [POSITIVE, 0.8]
  2. "Strong earnings beat expectations" [POSITIVE, 0.9]
  3. "Supply chain concerns" [NEGATIVE, -0.3]
  
Overall Sentiment: POSITIVE (0.4 average)
Correlation: Strong (positive news + price increase)
```

This helps you understand **why** the price moved!



