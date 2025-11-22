import { useEffect, useRef } from 'react';

// callbacks: onOpen, onMessage, onClose, onError
// Extended with: throttleMs (milliseconds between onMessage calls) & disabled flag
export default function useWebsocket(
    url,
    { onOpen, onMessage, onClose, onError, throttleMs = 0, disabled = false } = {},
    autoConnect = true
) {
    const wsRef = useRef(null);
    const lastEmitRef = useRef(0);

    useEffect(() => {
        if (!autoConnect || !url || disabled) return;
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = (e) => { if (onOpen) onOpen(e); };
        ws.onmessage = (e) => {
            if (!onMessage) return;
            try {
                const now = performance.now();
                if (throttleMs > 0 && now - lastEmitRef.current < throttleMs) return;
                lastEmitRef.current = now;
                onMessage(JSON.parse(e.data));
            } catch (err) {
                if (onError) onError(err);
            }
        };
        ws.onclose = (e) => { if (onClose) onClose(e); };
        ws.onerror = (e) => { if (onError) onError(e); };

        return () => {
            try { ws.close(); } catch (_) {}
        };
    }, [url, autoConnect, disabled, throttleMs, onOpen, onMessage, onClose, onError]);

    return { wsRef };
}