import { health } from '@/services/scamshield';

let cachedVersion: string | null = null;
let fetchPromise: Promise<string> | null = null;

export async function getAppVersion(): Promise<string> {
  if (cachedVersion) return cachedVersion;
  if (fetchPromise) return fetchPromise;

  fetchPromise = (async () => {
    try {
      const data = await health();
      cachedVersion = data.build_version || data.version;
      return cachedVersion;
    } catch {
      return 'unknown';
    }
  })();

  return fetchPromise;
}

export function getBuildTimestamp(): string {
  return import.meta.env.BUILD_TIMESTAMP || '';
}
