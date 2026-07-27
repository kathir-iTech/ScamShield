interface DiagnosticsEvent {
  type: string;
  message: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

const MAX_EVENTS = 100;

class FrontendDiagnostics {
  private events: DiagnosticsEvent[] = [];
  private apiFailures: number = 0;
  private renderErrors: number = 0;
  private networkErrors: number = 0;
  private buildTimestamp: string = import.meta.env.BUILD_TIMESTAMP || '';
  private appVersion: string = '';

  private add(type: string, message: string, details?: Record<string, unknown>) {
    const event: DiagnosticsEvent = {
      type,
      message,
      timestamp: new Date().toISOString(),
      details,
    };
    this.events.push(event);
    if (this.events.length > MAX_EVENTS) {
      this.events.shift();
    }
  }

  recordApiFailure(endpoint: string, status: number, message: string) {
    this.apiFailures++;
    this.networkErrors++;
    this.add('api_failure', `${endpoint} (${status}): ${message}`, {
      endpoint,
      status,
    });
  }

  recordRenderError(error: Error, component?: string) {
    this.renderErrors++;
    this.add('render_error', error.message, {
      component,
      stack: error.stack,
    });
  }

  recordNetworkError(message: string) {
    this.networkErrors++;
    this.add('network_error', message);
  }

  setAppVersion(version: string) {
    this.appVersion = version;
  }

  getSummary() {
    return {
      apiFailures: this.apiFailures,
      renderErrors: this.renderErrors,
      networkErrors: this.networkErrors,
      totalEvents: this.events.length,
      appVersion: this.appVersion,
      buildTimestamp: this.buildTimestamp,
    };
  }

  getRecentEvents(count: number = 10) {
    return this.events.slice(-count);
  }

  clear() {
    this.events = [];
    this.apiFailures = 0;
    this.renderErrors = 0;
    this.networkErrors = 0;
  }
}

export const diagnostics = new FrontendDiagnostics();
