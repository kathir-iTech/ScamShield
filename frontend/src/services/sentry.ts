import * as Sentry from '@sentry/react';

const dsn = import.meta.env.VITE_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_APP_ENV || 'production',
    tracesSampleRate: 0.1,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({ maskAllText: true, blockAllMedia: true }),
    ],
    beforeSend(event) {
      if (event.exception) {
        const msg = event.exception.values?.[0]?.value || '';
        if (msg.includes('ChunkLoadError') || msg.includes('Loading chunk')) {
          return null;
        }
      }
      return event;
    },
  });
}

export default Sentry;
