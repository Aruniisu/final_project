/**
 * useSocket — Real-time platform events hook
 * ============================================
 * Features:
 * - Infinite reconnection attempts
 * - Aggressive keepalive (1 min ping)
 * - Auto-reconnect on transport close
 * - Client wake signal (after screen off)
 * - Event replay on connect
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import io from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:5000';

// ============================================
// Singleton socket + listeners
// ============================================
let globalSocket = null;
const listeners = new Set();

function getSocket() {
    if (!globalSocket || !globalSocket.connected) {
        if (globalSocket) {
            try { globalSocket.disconnect(); } catch {}
        }

        globalSocket = io(WS_URL, {
            transports: ['polling', 'websocket'],
            reconnection: true,
            reconnectionAttempts: Infinity,     // ⭐ Never give up
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            randomizationFactor: 0.5,
            timeout: 30000,
            // ⭐ Aggressive keepalive
            pingInterval: 25000,
            pingTimeout: 60000,
            // ⭐ Auto-reconnect on visibility change
            autoConnect: true,
        });

        // ── Connect ──
        globalSocket.on('connect', () => {
            console.log('🔌 [Socket] Connected');
            // ⭐ Signal backend — client woke up
            try {
                globalSocket.emit('client_wake', { ts: Date.now() });
            } catch (e) {}
        });

        // ── Disconnect ──
        globalSocket.on('disconnect', (reason) => {
            console.log('🔌 [Socket] Disconnected:', reason);

            // ⭐ Immediate reconnect on transport close / ping timeout
            if (reason === 'transport close' || reason === 'ping timeout' || reason === 'transport error') {
                setTimeout(() => {
                    try {
                        if (!globalSocket.connected) {
                            globalSocket.connect();
                            console.log('🔌 [Socket] Reconnect attempted');
                        }
                    } catch (e) {
                        console.warn('Reconnect failed:', e);
                    }
                }, 500);
            }
        });

        // ── Reconnect events ──
        globalSocket.io.on('reconnect', (attempt) => {
            console.log('🔌 [Socket] Reconnected after', attempt, 'attempt(s)');
        });

        globalSocket.io.on('reconnect_attempt', (attempt) => {
            console.log('🔌 [Socket] Reconnect attempt', attempt);
        });

        globalSocket.io.on('reconnect_failed', () => {
            console.warn('🔌 [Socket] Reconnect failed — will retry');
        });

        // ── Platform events (main channel) ──
        globalSocket.on('platform_event', (event) => {
            listeners.forEach(fn => {
                try { fn(event); } catch (e) { console.error(e); }
            });
        });

        // ── Event replay on reconnect ──
        globalSocket.on('platform_events_replay', (data) => {
            (data.events || []).forEach(event => {
                listeners.forEach(fn => {
                    try { fn(event); } catch (e) {}
                });
            });
        });

        // ── Legacy channels ──
        ['live_log', 'chat_response', 'deploy_complete', 'action_response', 'agent_log']
            .forEach(evt => {
                globalSocket.on(evt, (data) => {
                    listeners.forEach(fn => {
                        try {
                            fn({ type: evt, data, timestamp: Date.now() });
                        } catch (e) {}
                    });
                });
            });

        // ── Visibility change → force reconnect if needed ──
        if (typeof document !== 'undefined') {
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') {
                    console.log('👁️ Tab visible — checking socket');
                    if (globalSocket && !globalSocket.connected) {
                        console.log('👁️ Socket dead — reconnecting');
                        globalSocket.connect();
                    } else if (globalSocket && globalSocket.connected) {
                        // Signal wake even if connected (fresh state)
                        try {
                            globalSocket.emit('client_wake', { ts: Date.now() });
                        } catch (e) {}
                    }
                }
            });
        }
    }
    return globalSocket;
}

// ============================================
// useSocket Hook
// ============================================
export function useSocket({ onEvent, filter } = {}) {
    const [connected, setConnected] = useState(false);
    const [lastEvent, setLastEvent] = useState(null);
    const handlerRef = useRef(onEvent);
    const filterRef = useRef(filter);

    useEffect(() => { handlerRef.current = onEvent; }, [onEvent]);
    useEffect(() => { filterRef.current = filter; }, [filter]);

    useEffect(() => {
        const socket = getSocket();

        const listener = (event) => {
            // Filter check
            if (filterRef.current && !filterRef.current.includes(event.type)) {
                return;
            }

            setLastEvent(event);

            if (handlerRef.current) {
                try {
                    handlerRef.current(event);
                } catch (e) {
                    console.error('Event handler error:', e);
                }
            }
        };

        listeners.add(listener);

        // Connection state
        const onConnect = () => setConnected(true);
        const onDisconnect = () => setConnected(false);

        socket.on('connect', onConnect);
        socket.on('disconnect', onDisconnect);
        setConnected(socket.connected);

        return () => {
            listeners.delete(listener);
            socket.off('connect', onConnect);
            socket.off('disconnect', onDisconnect);
        };
    }, []);

    return { connected, lastEvent };
}

// ============================================
// useSocketEmit — Helper to emit events
// ============================================
export function useSocketEmit() {
    return useCallback((event, data) => {
        const socket = getSocket();
        socket.emit(event, data);
    }, []);
}

export default useSocket;