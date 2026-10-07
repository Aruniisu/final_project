/**
 * useSessionTimeout — Auto-logout after inactivity
 * Respects user's sessionTimeout setting (in minutes)
 */
import { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSettings } from '../context/SettingsContext';
import toast from 'react-hot-toast';

const ACTIVITY_EVENTS = ['mousedown', 'keydown', 'touchstart', 'scroll', 'click'];

export const useSessionTimeout = () => {
  const { isAuthenticated, logout } = useAuth();
  const { settings } = useSettings();
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!isAuthenticated) return;

    const timeoutMinutes = settings.sessionTimeout || 30;
    const timeoutMs = timeoutMinutes * 60 * 1000;

    const resetTimer = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        toast.error(`Session expired after ${timeoutMinutes} minutes of inactivity`);
        logout();
      }, timeoutMs);
    };

    // Initialize
    resetTimer();

    // Reset on activity
    ACTIVITY_EVENTS.forEach((evt) =>
      window.addEventListener(evt, resetTimer, { passive: true })
    );

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      ACTIVITY_EVENTS.forEach((evt) =>
        window.removeEventListener(evt, resetTimer)
      );
    };
  }, [isAuthenticated, settings.sessionTimeout, logout]);
};

export default useSessionTimeout;