import { useEffect, useRef, useCallback } from 'react';
import { API_BASE } from '../services/api';

interface NewsItem {
  id: string;
  title: string;
  url: string;
  source: string;
  company: string;
  publishedAt: string;
  symbol?: string;
  sentiment?: {
    label: string;
    score: number;
  };
}

interface WebSocketMessage {
  type: 'news_update' | 'ping';
  news?: NewsItem[];
  timestamp: string;
}

interface UseNewsWebSocketOptions {
  onNewsUpdate: (news: NewsItem[]) => void;
  autoReconnect?: boolean;
  reconnectDelay?: number;
}

export const useNewsWebSocket = ({
  onNewsUpdate,
  autoReconnect = true,
  reconnectDelay = 3000,
}: UseNewsWebSocketOptions) => {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | undefined>(undefined);
  const isConnecting = useRef(false);
  const isMounted = useRef(true);

  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (ws.current?.readyState === WebSocket.OPEN ||
        ws.current?.readyState === WebSocket.CONNECTING ||
        isConnecting.current) {
      console.log('[WebSocket] Already connected or connecting, skipping...');
      return;
    }

    isConnecting.current = true;
    console.log('[WebSocket] Connecting to news WebSocket...');

    try {
      // Convert HTTP(S) to WS(S)
      const wsUrl = API_BASE.replace(/^http/, 'ws');
      const socket = new WebSocket(`${wsUrl}/ws/news`);

      socket.onopen = () => {
        console.log('[WebSocket] ✅ Connected to news feed');
        isConnecting.current = false;
      };

      socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === 'news_update' && message.news) {
            console.log('[WebSocket] 📰 Received', message.news.length, 'new articles');
            onNewsUpdate(message.news);
          } else if (message.type === 'ping') {
            // Server ping to keep connection alive
            console.log('[WebSocket] 🏓 Ping received');
          }
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('[WebSocket] ❌ Error:', error);
        isConnecting.current = false;
      };

      socket.onclose = (event) => {
        console.log('[WebSocket] 🔌 Disconnected from news feed', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        isConnecting.current = false;

        // Only clear ws.current if it's still this socket
        if (ws.current === socket) {
          ws.current = null;
        }

        // Auto-reconnect only if: enabled, still mounted, and not a clean close
        if (autoReconnect && isMounted.current && ws.current === null && !event.wasClean) {
          console.log(`[WebSocket] Reconnecting in ${reconnectDelay}ms...`);
          reconnectTimeout.current = setTimeout(connect, reconnectDelay);
        }
      };

      ws.current = socket;
    } catch (error) {
      console.error('[WebSocket] Failed to connect:', error);
      isConnecting.current = false;

      if (autoReconnect) {
        reconnectTimeout.current = setTimeout(connect, reconnectDelay);
      }
    }
  }, [onNewsUpdate, autoReconnect, reconnectDelay]);

  const disconnect = useCallback(() => {
    console.log('[WebSocket] Disconnecting...');

    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = undefined;
    }

    if (ws.current) {
      // Prevent onclose from triggering reconnect
      const socket = ws.current;
      ws.current = null;

      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
    }

    isConnecting.current = false;
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    isMounted.current = true;

    // Small delay to avoid React Strict Mode double-mount issues
    const timer = setTimeout(() => {
      if (isMounted.current) {
        connect();
      }
    }, 100);

    return () => {
      isMounted.current = false;
      clearTimeout(timer);
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected: ws.current?.readyState === WebSocket.OPEN,
    disconnect,
    reconnect: connect,
  };
};
