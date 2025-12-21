// Sentiment Analysis Agent - Analyzes price movements and correlates with market sentiment

import { analyzeSentiment, fetchNewsWithSentiment, correlateNewsWithPrice, type NewsArticle, type SentimentAnalysis } from './newsService';
import { fetchStockData, type StockQuote } from './stockDataService';
import { analyzePriceSentiment, type PriceSentiment, type NasdaqStockData } from './priceSentimentService';

export interface PriceEvent {
  timestamp: number;
  price: number;
  change: number;
  changePercent: number;
  correlatedNews: NewsArticle[];
  sentimentImpact: {
    averageSentiment: number;
    dominantSentiment: 'positive' | 'negative' | 'neutral';
    newsCount: number;
  };
}

export class SentimentAgent {
  private symbol: string;
  private priceHistory: Array<{ time: number; price: number }> = [];
  private newsCache: Map<string, NewsArticle[]> = new Map();

  constructor(symbol: string) {
    this.symbol = symbol;
  }

  // Analyze price movement and find correlated news
  async analyzePriceEvent(
    currentPrice: number,
    previousPrice: number,
    timestamp: number
  ): Promise<PriceEvent> {
    const change = currentPrice - previousPrice;
    const changePercent = (change / previousPrice) * 100;

    // Fetch recent news
    const news = await this.getRecentNews(timestamp);
    
    // Filter news within time window (last 2 hours)
    const timeWindow = 2 * 3600 * 1000; // 2 hours in milliseconds
    const relevantNews = news.filter((article) => {
      const articleTime = new Date(article.publishedAt).getTime();
      return Math.abs(articleTime - timestamp) < timeWindow;
    });

    // Calculate sentiment impact
    const sentimentImpact = this.calculateSentimentImpact(relevantNews);

    return {
      timestamp,
      price: currentPrice,
      change,
      changePercent,
      correlatedNews: relevantNews,
      sentimentImpact,
    };
  }

  // Get recent news (with caching)
  private async getRecentNews(timestamp: number): Promise<NewsArticle[]> {
    const cacheKey = `${this.symbol}-${Math.floor(timestamp / (3600 * 1000))}`; // Cache per hour
    
    if (this.newsCache.has(cacheKey)) {
      return this.newsCache.get(cacheKey)!;
    }

    const news = await fetchNewsWithSentiment(this.symbol, 20);
    this.newsCache.set(cacheKey, news);
    
    // Clean old cache entries (keep last 24 hours)
    const maxAge = 24 * 3600 * 1000;
    for (const [key, _] of this.newsCache.entries()) {
      const keyTimestamp = parseInt(key.split('-')[1]) * 3600 * 1000;
      if (timestamp - keyTimestamp > maxAge) {
        this.newsCache.delete(key);
      }
    }

    return news;
  }

  // Calculate sentiment impact from news
  private calculateSentimentImpact(news: NewsArticle[]): {
    averageSentiment: number;
    dominantSentiment: 'positive' | 'negative' | 'neutral';
    newsCount: number;
  } {
    if (news.length === 0) {
      return {
        averageSentiment: 0,
        dominantSentiment: 'neutral',
        newsCount: 0,
      };
    }

    const sentiments = news
      .map((article) => article.sentiment?.score || 0)
      .filter((score) => score !== 0);

    const averageSentiment =
      sentiments.length > 0
        ? sentiments.reduce((sum, score) => sum + score, 0) / sentiments.length
        : 0;

    let dominantSentiment: 'positive' | 'negative' | 'neutral' = 'neutral';
    if (averageSentiment > 0.2) dominantSentiment = 'positive';
    else if (averageSentiment < -0.2) dominantSentiment = 'negative';

    return {
      averageSentiment,
      dominantSentiment,
      newsCount: news.length,
    };
  }

  // Monitor price and detect significant movements
  async monitorPriceMovement(
    currentPrice: number,
    timestamp: number
  ): Promise<PriceEvent | null> {
    if (this.priceHistory.length === 0) {
      this.priceHistory.push({ time: timestamp, price: currentPrice });
      return null;
    }

    const previousPrice = this.priceHistory[this.priceHistory.length - 1].price;
    const changePercent = Math.abs((currentPrice - previousPrice) / previousPrice) * 100;

    // Only analyze if price moved significantly (>0.5%)
    if (changePercent > 0.5) {
      const event = await this.analyzePriceEvent(currentPrice, previousPrice, timestamp);
      this.priceHistory.push({ time: timestamp, price: currentPrice });
      
      // Keep only last 100 price points
      if (this.priceHistory.length > 100) {
        this.priceHistory.shift();
      }
      
      return event;
    }

    this.priceHistory.push({ time: timestamp, price: currentPrice });
    return null;
  }

  // Get news summary for a time period
  async getNewsSummary(
    startTime: number,
    endTime: number
  ): Promise<{
    news: NewsArticle[];
    sentiment: SentimentAnalysis;
    priceCorrelation: number;
  }> {
    const news = await fetchNewsWithSentiment(this.symbol, 50);
    const relevantNews = news.filter((article) => {
      const articleTime = new Date(article.publishedAt).getTime();
      return articleTime >= startTime && articleTime <= endTime;
    });

    const sentiment = this.calculateSentimentImpact(relevantNews);
    
    // Calculate price correlation (simplified)
    const priceCorrelation = this.calculatePriceCorrelation(relevantNews, startTime, endTime);

    return {
      news: relevantNews,
      sentiment: {
        score: sentiment.averageSentiment,
        label: sentiment.dominantSentiment,
        confidence: Math.abs(sentiment.averageSentiment),
        keywords: [],
        summary: `${sentiment.newsCount} articles found. Dominant sentiment: ${sentiment.dominantSentiment}`,
      },
      priceCorrelation,
    };
  }

  private calculatePriceCorrelation(
    news: NewsArticle[],
    startTime: number,
    endTime: number
  ): number {
    // Simplified correlation: positive news should correlate with price increases
    if (news.length === 0) return 0;

    const positiveNews = news.filter(
      (article) => article.sentiment?.label === 'positive'
    ).length;
    const negativeNews = news.filter(
      (article) => article.sentiment?.label === 'negative'
    ).length;

    // Correlation score: -1 to 1
    const correlation = (positiveNews - negativeNews) / news.length;
    return correlation;
  }

  // Analyze sentiment based on NASDAQ price data
  analyzePriceBasedSentiment(stockData: NasdaqStockData): PriceSentiment {
    return analyzePriceSentiment(stockData);
  }

  // Get simple sentiment from price data
  getSimpleSentiment(stockData: NasdaqStockData): SentimentAnalysis {
    const priceSentiment = analyzePriceSentiment(stockData);

    return {
      score: priceSentiment.score,
      label: priceSentiment.score > 0.1 ? 'positive' : priceSentiment.score < -0.1 ? 'negative' : 'neutral',
      confidence: priceSentiment.confidence,
      keywords: [],
      summary: priceSentiment.summary,
    };
  }
}



