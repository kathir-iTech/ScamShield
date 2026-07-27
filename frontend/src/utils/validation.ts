import { z } from 'zod';

export const textAnalysisSchema = z.object({
  text: z
    .string()
    .min(1, 'Text is required')
    .max(10000, 'Text must not exceed 10,000 characters'),
});

export const imageAnalysisSchema = z.object({
  file: z
    .instanceof(File)
    .refine((f) => f.size > 0, 'File is required')
    .refine(
      (f) => ['image/jpeg', 'image/png', 'image/webp', 'image/bmp'].includes(f.type),
      'File must be a supported image type (JPEG, PNG, WebP, BMP)'
    )
    .refine((f) => f.size <= 10 * 1024 * 1024, 'File must not exceed 10 MB'),
});


