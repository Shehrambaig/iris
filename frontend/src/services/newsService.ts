// News Service - Fetches and analyzes news related to stocks
import { API_BASE } from './api';

export interface NewsArticle {
  id: string;
  title: string;
  content: string;
  source: string;
  publishedAt: string;
  url: string;
  symbol?: string;
  sentiment?: SentimentAnalysis;
  priceAtTime?: number;
}

export interface SentimentAnalysis {
  score: number; // -1 to 1 (negative to positive)
  label: 'positive' | 'negative' | 'neutral';
  confidence: number; // 0 to 1
  keywords: string[];
  summary: string;
}

const API_BASE_URL = API_BASE;

// Fetch news for a specific symbol
export const fetchNewsForSymbol = async (
  symbol: string,
  limit: number = 10
): Promise<NewsArticle[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/news/${symbol}?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch news');
    const data = await response.json();
    return data.map((article: any) => ({
      id: article.id || article.url || Math.random().toString(),
      title: article.title || '',
      content: article.content || article.description || '',
      source: article.source || 'Unknown',
      publishedAt: article.publishedAt || article.published_at || new Date().toISOString(),
      url: article.url || '',
      symbol: symbol,
      sentiment: article.sentiment,
      priceAtTime: article.priceAtTime,
    }));
  } catch (error) {
    console.error(`Error fetching news for ${symbol}:`, error);
    return [];
  }
};

// Analyze sentiment of news article
export const analyzeSentiment = async (text: string): Promise<SentimentAnalysis> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sentiment/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) throw new Error('Failed to analyze sentiment');
    const data = await response.json();
    return {
      score: data.score || 0,
      label: data.label || 'neutral',
      confidence: data.confidence || 0.5,
      keywords: data.keywords || [],
      summary: data.summary || '',
    };
  } catch (error) {
    console.error('Error analyzing sentiment:', error);
    // Fallback to basic sentiment analysis
    return performBasicSentimentAnalysis(text);
  }
};

// Basic sentiment analysis fallback (client-side)
const performBasicSentimentAnalysis = (text: string): SentimentAnalysis => {
  const lowerText = text.toLowerCase();
  const positiveWords = ['up', 'rise', 'gain', 'surge', 'growth', 'profit', 'success', 'positive', 'strong', 'beat', 'exceed'];
  const negativeWords = ['down', 'fall', 'drop', 'decline', 'loss', 'fail', 'negative', 'weak', 'miss', 'below', 'concern'];
  
  let positiveCount = 0;
  let negativeCount = 0;
  
  positiveWords.forEach(word => {
    if (lowerText.includes(word)) positiveCount++;
  });
  
  negativeWords.forEach(word => {
    if (lowerText.includes(word)) negativeCount++;
  });
  
  const total = positiveCount + negativeCount;
  const score = total > 0 ? (positiveCount - negativeCount) / total : 0;
  
  let label: 'positive' | 'negative' | 'neutral' = 'neutral';
  if (score > 0.2) label = 'positive';
  else if (score < -0.2) label = 'negative';
  
  return {
    score,
    label,
    confidence: Math.abs(score),
    keywords: [],
    summary: '',
  };
};

// Fetch news with sentiment analysis
export const fetchNewsWithSentiment = async (
  symbol: string,
  limit: number = 10
): Promise<NewsArticle[]> => {
  const articles = await fetchNewsForSymbol(symbol, limit);
  
  // Analyze sentiment for each article
  const articlesWithSentiment = await Promise.all(
    articles.map(async (article) => {
      if (!article.sentiment && article.content) {
        const sentiment = await analyzeSentiment(article.content);
        return { ...article, sentiment };
      }
      return article;
    })
  );
  
  return articlesWithSentiment;
};

// Correlate news with price movements
export const correlateNewsWithPrice = async (
  symbol: string,
  priceHistory: Array<{ time: number; price: number }>
): Promise<Array<{ time: number; price: number; news: NewsArticle[] }>> => {
  const news = await fetchNewsWithSentiment(symbol, 50);
  
  // Group news by time periods and match with price movements
  return priceHistory.map((pricePoint) => {
    const timeWindow = 3600; // 1 hour window
    const relevantNews = news.filter((article) => {
      const articleTime = new Date(article.publishedAt).getTime() / 1000;
      return Math.abs(articleTime - pricePoint.time) < timeWindow;
    });
    
    return {
      time: pricePoint.time,
      price: pricePoint.price,
      news: relevantNews,
    };
  });
};



