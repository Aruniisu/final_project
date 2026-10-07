/**
 * useWakeLock — Keep screen + network awake during active operations.
 * Only works when tab is visible (browser restriction).
 */
import { useEffect, useRef, useState } from 'react';

export function useWakeLock(active = true) {
  const sentinelRef = useRef(null);
  const [isLocked, setIsLocked] = useState(false);

  useEffect(() => {
    if (!active) return;
    if (!('wakeLock' in navigator)) {
      console.warn('Wake Lock API not supported');
      return;
    }

    let cancelled = false;

    const request = async () => {
      try {
        if (cancelled) return;
        sentinelRef.current = await navigator.wakeLock.request('screen');
        setIsLocked(true);
        console.log('🔒 Wake Lock active');

        sentinelRef.current.addEventListener('release', () => {
          setIsLocked(false);
          console.log('🔓 Wake Lock released');
        });
      } catch (err) {
        console.warn('Wake Lock failed:', err);
        setIsLocked(false);
      }
    };

    request();

    // Re-request when tab becomes visible again
    const onVisibility = () => {
      if (document.visibilityState === 'visible' && !cancelled) {
        request();
      }
    };
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      cancelled = true;
      document.removeEventListener('visibilitychange', onVisibility);
      if (sentinelRef.current) {
        try { sentinelRef.current.release(); } catch {}
      }
    };
  }, [active]);

  return isLocked;
}

export default useWakeLock;