// Analytics: always batch-POST to /api/events; forward to Amplitude only if a key is configured
// (lazy-loaded so the bundle stays lean and the no-key path is a true no-op).

import type { AnalyticsEvent, Device, Locale } from "@/types/contract";
import { sendEvents } from "@/api/client";
import { currentLocale } from "@/i18n";

const SCHEMA_VERSION = 1;
const SESSION_STORAGE_KEY = "onboarding_session_id";
const FLUSH_INTERVAL_MS = 4000;
const MAX_BATCH = 20;

const AMPLITUDE_API_KEY = import.meta.env.VITE_AMPLITUDE_API_KEY ?? "";

let queue: AnalyticsEvent[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;
let amplitudeReady: Promise<AmplitudeLike | null> | null = null;

interface AmplitudeLike {
  init: (key: string, options?: Record<string, unknown>) => void;
  track: (name: string, props?: Record<string, unknown>) => void;
}

function detectDevice(): Device {
  const coarse = window.matchMedia?.("(pointer: coarse)").matches ?? false;
  const narrow = window.matchMedia?.("(max-width: 767px)").matches ?? false;
  return coarse || narrow ? "mobile" : "desktop";
}

function sessionId(): string {
  let id = sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (id == null) {
    id = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem(SESSION_STORAGE_KEY, id);
  }
  return id;
}

async function loadAmplitude(): Promise<AmplitudeLike | null> {
  if (AMPLITUDE_API_KEY.length === 0) {
    return null;
  }
  if (amplitudeReady == null) {
    // Specifier kept in a variable so the bundler/TS treats it as optional and does not
    // require the package to be installed when no Amplitude key is configured.
    const moduleSpecifier = "@amplitude/analytics-browser";
    amplitudeReady = import(/* @vite-ignore */ moduleSpecifier)
      .then((module) => {
        const amplitude = module as unknown as AmplitudeLike;
        amplitude.init(AMPLITUDE_API_KEY, { defaultTracking: false });
        return amplitude;
      })
      .catch(() => {
        return null;
      });
  }
  return amplitudeReady;
}

async function flush(): Promise<void> {
  if (flushTimer != null) {
    clearTimeout(flushTimer);
    flushTimer = null;
  }
  if (queue.length === 0) {
    return;
  }
  const batch = queue;
  queue = [];
  try {
    await sendEvents(batch);
  } catch {
    // Analytics must never break the flow; drop the batch silently.
  }
  const amplitude = await loadAmplitude();
  if (amplitude != null) {
    for (const event of batch) {
      amplitude.track(event.name, { onboarding_id: event.onboarding_id, ...event.props });
    }
  }
}

function scheduleFlush(): void {
  if (queue.length >= MAX_BATCH) {
    void flush();
    return;
  }
  if (flushTimer == null) {
    flushTimer = setTimeout(() => {
      void flush();
    }, FLUSH_INTERVAL_MS);
  }
}

export interface Analytics {
  track: (name: string, onboardingId: string, props?: Record<string, unknown>) => void;
  flush: () => Promise<void>;
  device: () => Device;
}

export function useAnalytics(): Analytics {
  function track(name: string, onboardingId: string, props?: Record<string, unknown>): void {
    const event: AnalyticsEvent = {
      name: name,
      onboarding_id: onboardingId,
      session_id: sessionId(),
      device: detectDevice(),
      locale: currentLocale() as Locale,
      schema_version: SCHEMA_VERSION,
      ts: new Date().toISOString(),
      props: props,
    };
    queue.push(event);
    scheduleFlush();
  }

  return { track: track, flush: flush, device: detectDevice };
}

if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    void flush();
  });
}
