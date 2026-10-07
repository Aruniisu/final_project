/**
 * usePlatformEvents — Easy page integration
 */

import useSocket from './useSocket';

const PAGE_EVENTS = {
    dashboard: [
        'process:started', 'process:stopped', 'process:crashed', 'process:registered',
        'pipeline:deployed', 'pipeline:failed', 'pipeline:started',
        'assistant:launched',
        'monitoring:alert', 'monitoring:resolved',
        'training:started', 'training:completed', 'training:failed',
        'agent:action', 'agent:mode_changed', 'agent:reaction',
        'fixer:log',
    ],
    assistant: [
        'process:started', 'process:stopped', 'process:crashed',
        'pipeline:deployed', 'pipeline:failed',
        'agent:action', 'agent:mode_changed',
        'fixer:log',
    ],
    pipeline: [
        'process:started', 'process:stopped', 'process:crashed',
        'pipeline:deployed', 'pipeline:failed',
        'agent:action',
        'fixer:log',
    ],
    infrastructure: [
        'process:started', 'process:stopped', 'process:crashed', 'process:registered',
        'pipeline:deployed', 'pipeline:failed',
        'assistant:launched',
        'monitoring:alert', 'monitoring:resolved',
        'training:started', 'training:completed',
        'agent:action', 'agent:mode_changed', 'agent:reaction',
        'settings:updated', 'settings:agent_config',
        'fixer:log',
    ],
    monitoring: [
        'process:started', 'process:stopped', 'process:crashed',
        'pipeline:deployed', 'pipeline:failed',
        'monitoring:alert', 'monitoring:resolved',
        'agent:action',
        'fixer:log',
    ],
    training: [
        'process:started', 'process:stopped',
        'training:started', 'training:completed', 'training:failed',
        'agent:action',
        'fixer:log',
    ],
    settings: [
        'agent:mode_changed', 'settings:updated',
        'fixer:log',
    ],
};

export function usePlatformEvents(pageName, onEventOrEvents, onRefresh) {
    let customFilter = null;
    let callback = onEventOrEvents;

    if (Array.isArray(onEventOrEvents)) {
        customFilter = onEventOrEvents;
        callback = onRefresh;
    }

    const defaultFilter = PAGE_EVENTS[pageName] || [];
    const filter = customFilter || defaultFilter;

    useSocket({
        filter,
        onEvent: (evt) => {
            console.log(`📡 [${pageName}]`, evt.type, evt.data);
            if (callback) {
                try { callback(evt); } catch (e) { console.error(e); }
            }
        },
    });
}

export default usePlatformEvents;