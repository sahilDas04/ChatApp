import { useEffect, useRef, useCallback } from 'react';

const WS_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1')
  .replace(/^http/, 'ws');

/**
 * useWebSocket — connects to the backend WS endpoint for a room.
 * @param {number|null} roomId
 * @param {function} onMessage  called with parsed JSON data on every message
 */
export default function useWebSocket(roomId, onMessage) {
  const wsRef = useRef(null);
  const onMessageRef = useRef(onMessage);
  const reconnectTimer = useRef(null);
  const reconnectDelay = useRef(1000);

  // Keep callback ref fresh
  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (!token || !roomId) return;

    const url = `${WS_BASE}/ws/${roomId}?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectDelay.current = 1000;
      // Keep-alive ping every 25 s
      ws._pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== 'pong') onMessageRef.current(data);
      } catch { /* ignore bad frames */ }
    };

    ws.onclose = () => {
      clearInterval(ws._pingInterval);
      // Auto-reconnect with backoff
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => ws.close();
  }, [roomId]);

  useEffect(() => {
    if (!roomId) return;
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        clearInterval(wsRef.current._pingInterval);
        wsRef.current.onclose = null; // prevent reconnect on unmount
        wsRef.current.close();
      }
    };
  }, [roomId, connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const sendTyping = useCallback((isTyping) => {
    send({ type: 'typing', is_typing: isTyping });
  }, [send]);

  return { send, sendTyping };
}
