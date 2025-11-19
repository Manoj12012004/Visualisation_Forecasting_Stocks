import { useEffect, useRef } from 'react';

// callbacks: onOpen, onMessage
export default function useWebsocket(url, { onOpen, onMessage, onClose, onError } = {}, autoConnect = true) {
    const wsRef = useRef(null);

    useEffect(() => {
        if (!autoConnect || !url) return;
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = (e) => { if (onOpen) onOpen(e); };
        ws.onmessage = (e) => { if (onMessage) onMessage(JSON.parse(e.data)); };
        ws.onclose = (e) => { if (onClose) onClose(e); };
        ws.onerror = (e) => { if (onError) onError(e); };

        return () => {
            try { ws.close(); } catch (err) {}
        };
    }, [url, autoConnect, onOpen, onMessage, onClose, onError]);

    return { wsRef };

}