interface LogEntry {
  level: 'info' | 'warn' | 'error';
  message: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

const MAX_LOGS = 200;
const logs: LogEntry[] = [];

function addLog(level: LogEntry['level'], message: string, data?: Record<string, unknown>) {
  const entry: LogEntry = { level, message, data, timestamp: new Date().toISOString() };
  logs.push(entry);
  if (logs.length > MAX_LOGS) logs.shift();

  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (dsn && level === 'error') {
    try {
      fetch(`${dsn}/envelope/`, {
        method: 'POST',
        body: JSON.stringify({ message, data, timestamp: entry.timestamp }),
      }).catch(() => {});
    } catch {}
  }
}

export const monitor = {
  info: (message: string, data?: Record<string, unknown>) => addLog('info', message, data),
  warn: (message: string, data?: Record<string, unknown>) => addLog('warn', message, data),
  error: (message: string, data?: Record<string, unknown>) => addLog('error', message, data),
  getLogs: () => [...logs],
  clear: () => { logs.length = 0; },
};
