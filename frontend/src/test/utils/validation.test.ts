import { describe, it, expect } from 'vitest';
import { textAnalysisSchema, imageAnalysisSchema } from '@/utils/validation';

describe('textAnalysisSchema', () => {
  it('accepts valid text', () => {
    const result = textAnalysisSchema.parse({ text: 'Hello world' });
    expect(result.text).toBe('Hello world');
  });

  it('rejects empty text', () => {
    expect(() => textAnalysisSchema.parse({ text: '' })).toThrow();
  });

  it('rejects text over 10000 characters', () => {
    expect(() => textAnalysisSchema.parse({ text: 'a'.repeat(10001) })).toThrow();
  });

  it('accepts text at exactly 10000 characters', () => {
    const result = textAnalysisSchema.parse({ text: 'a'.repeat(10000) });
    expect(result.text).toHaveLength(10000);
  });
});

describe('imageAnalysisSchema', () => {
  const createFile = (name: string, type: string, size: number) => {
    const blob = new Blob(['x'.repeat(size)], { type });
    return new File([blob], name, { type });
  };

  it('accepts valid JPEG', () => {
    const file = createFile('test.jpg', 'image/jpeg', 1024);
    const result = imageAnalysisSchema.parse({ file });
    expect(result.file.name).toBe('test.jpg');
  });

  it('accepts valid PNG', () => {
    const file = createFile('test.png', 'image/png', 1024);
    expect(() => imageAnalysisSchema.parse({ file })).not.toThrow();
  });

  it('rejects empty file', () => {
    const file = createFile('empty.jpg', 'image/jpeg', 0);
    expect(() => imageAnalysisSchema.parse({ file })).toThrow();
  });

  it('rejects unsupported file type', () => {
    const file = createFile('test.gif', 'image/gif', 1024);
    expect(() => imageAnalysisSchema.parse({ file })).toThrow();
  });

  it('rejects file over 10MB', () => {
    const file = createFile('large.jpg', 'image/jpeg', 11 * 1024 * 1024);
    expect(() => imageAnalysisSchema.parse({ file })).toThrow();
  });
});
