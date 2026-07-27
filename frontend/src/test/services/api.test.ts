import { describe, it, expect } from 'vitest';

describe('api client', () => {
  it('creates axios instance with correct defaults', async () => {
    const mod = await import('@/services/api');
    const instance = mod.default;
    expect(instance.defaults.timeout).toBe(30000);
  });

  it('has base URL configured', async () => {
    const mod = await import('@/services/api');
    const instance = mod.default;
    expect(instance.defaults.baseURL).toBe('/api');
  });
});
