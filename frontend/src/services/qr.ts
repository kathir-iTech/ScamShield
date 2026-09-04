import jsQR from 'jsqr';

export interface QrDecodeResult {
  found: boolean;
  payload: string | null;
  type: 'url' | 'upi' | 'text' | null;
}

function classifyPayload(raw: string): QrDecodeResult {
  const trimmed = raw.trim();

  const urlMatch = trimmed.match(/^https?:\/\/\S+$/i);
  if (urlMatch) return { found: true, payload: trimmed, type: 'url' };

  const upiMatch = trimmed.match(/^[a-z0-9._-]+@[a-z]{3,}$/i);
  if (upiMatch) return { found: true, payload: trimmed, type: 'upi' };

  return { found: true, payload: trimmed, type: 'text' };
}

export async function decodeQrFromImage(file: File): Promise<QrDecodeResult> {
  const notFound: QrDecodeResult = { found: false, payload: null, type: null };

  try {
    const img = await loadImage(file);
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return notFound;

    ctx.drawImage(img, 0, 0);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

    const code = jsQR(imageData.data, canvas.width, canvas.height, {
      inversionAttempts: 'attemptBoth',
    });

    if (code?.data) return classifyPayload(code.data);
    return notFound;
  } catch {
    return notFound;
  }
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image for QR decode'));
    };
    img.src = url;
  });
}
