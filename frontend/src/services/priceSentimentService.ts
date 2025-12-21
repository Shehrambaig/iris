/**
 * Price-Based Sentiment Analysis Service
 * Analyzes sentiment based on live NASDAQ price data
 * Uses percentage change and volume to determine market sentiment
 */

export interface PriceSentiment {
  score: number; // -1 to 1 (negative to positive)
  label: 'very_positive' | 'positive' | 'slightly_positive' | 'neutral' | 'slightly_negative' | 'negative' | 'very_negative';
  confidence: number; // 0 to 1
  summary: string;
  source: 'price_action';
  pct_change: number;
  volume: number;
}

export interface NasdaqStockData {
  symbol: string;
  name: string;
  lastSale: string;
  change: string;
  pctChange: string;
  volume: string;
}

/**
 * Analyze sentiment based on NASDAQ price data
 * This matches the backend's analyze_price_sentiment logic
 */
export const analyzePriceSentiment = (stockData: NasdaqStockData): PriceSentiment => {
  try {
    // Extract percentage change (e.g., "+3.93%" -> 3.93)
    const pctChangeStr = stockData.pctChange || '0%';
    const pctChange = parseFloat(pctChangeStr.replace('%', '').replace('+', ''));

    // Extract volume (e.g., "324,925,927" -> 324925927)
    const volumeStr = stockData.volume || '0';
    const volume = parseInt(volumeStr.replace(/,/g, ''));

    // Calculate sentiment score based on percentage change
    // Score ranges from -1 (very negative) to +1 (very positive)
    let score: number;
    let label: PriceSentiment['label'];
    let summary: string;

    if (pctChange >= 5.0) {
      score = 1.0;
      label = 'very_positive';
      summary = `Strong rally: +${pctChange}%`;
    } else if (pctChange >= 2.0) {
      score = 0.7;
      label = 'positive';
      summary = `Good gains: +${pctChange}%`;
    } else if (pctChange >= 0.5) {
      score = 0.4;
      label = 'slightly_positive';
      summary = `Modest gains: +${pctChange}%`;
    } else if (pctChange > -0.5) {
      score = 0.0;
      label = 'neutral';
      summary = `Flat: ${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(2)}%`;
    } else if (pctChange > -2.0) {
      score = -0.4;
      label = 'slightly_negative';
      summary = `Modest decline: ${pctChange}%`;
    } else if (pctChange > -5.0) {
      score = -0.7;
      label = 'negative';
      summary = `Notable drop: ${pctChange}%`;
    } else {
      score = -1.0;
      label = 'very_negative';
      summary = `Sharp selloff: ${pctChange}%`;
    }

    // Calculate confidence based on volume
    // Higher volume = higher confidence in the sentiment
    // Average volume threshold: 100M shares (adjust based on typical volumes)
    const volumeConfidence = Math.min(volume / 100_000_000, 1.0); // Cap at 1.0
    const confidence = Math.max(0.5, volumeConfidence); // Minimum 50% confidence

    return {
      score: parseFloat(score.toFixed(3)),
      label,
      confidence: parseFloat(confidence.toFixed(3)),
      summary,
      source: 'price_action',
      pct_change: pctChange,
      volume,
    };
  } catch (error) {
    console.error('Error analyzing price sentiment:', error);
    return {
      score: 0.0,
      label: 'neutral',
      confidence: 0.1,
      summary: 'Unable to analyze price data',
      source: 'price_action',
      pct_change: 0,
      volume: 0,
    };
  }
};

/**
 * Get sentiment color for UI display
 */
export const getSentimentColor = (sentiment: PriceSentiment): string => {
  if (sentiment.score >= 0.6) return '#00ff00'; // Bright green
  if (sentiment.score >= 0.3) return '#7cfc00'; // Light green
  if (sentiment.score >= 0.1) return '#90ee90'; // Pale green
  if (sentiment.score > -0.1) return '#gray'; // Gray
  if (sentiment.score > -0.3) return '#ffb6c1'; // Light red
  if (sentiment.score > -0.6) return '#ff6b6b'; // Red
  return '#ff0000'; // Bright red
};

/**
 * Get sentiment emoji for UI display
 */
export const getSentimentEmoji = (sentiment: PriceSentiment): string => {
  if (sentiment.score >= 0.6) return '🚀';
  if (sentiment.score >= 0.3) return '📈';
  if (sentiment.score >= 0.1) return '⬆️';
  if (sentiment.score > -0.1) return '➡️';
  if (sentiment.score > -0.3) return '⬇️';
  if (sentiment.score > -0.6) return '📉';
  return '💥';
};

/**
 * Get sentiment label in simple format
 */
export const getSimpleSentimentLabel = (sentiment: PriceSentiment): 'positive' | 'negative' | 'neutral' => {
  if (sentiment.score > 0.1) return 'positive';
  if (sentiment.score < -0.1) return 'negative';
  return 'neutral';
};
