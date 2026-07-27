import sharp from 'sharp';
import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = join(__dirname, '..', 'public');

const SHIELD_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <path fill="#10b981" d="M16 2L4 8v8c0 9.94 12 16 12 16s12-6.06 12-16V8L16 2z"/>
  <path fill="#fff" d="M14.5 17.5L11 14l-1.5 1.5 5 5 8-8L21 11z"/>
</svg>`;

const OG_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#10b981"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="0" y="0" width="1200" height="630" fill="rgba(0,0,0,0.15)"/>
  
  <!-- Shield icon -->
  <g transform="translate(100, 180) scale(6)">
    <path fill="#fff" d="M16 2L4 8v8c0 9.94 12 16 12 16s12-6.06 12-16V8L16 2z"/>
    <path fill="#059669" d="M14.5 17.5L11 14l-1.5 1.5 5 5 8-8L21 11z"/>
  </g>

  <!-- Text -->
  <text x="250" y="300" font-family="system-ui, -apple-system, sans-serif" font-size="64" font-weight="700" fill="#fff">ScamShield</text>
  <text x="250" y="370" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="500" fill="#d1fae5">AI-Powered Scam Detection</text>

  <!-- Decorative dots -->
  <circle cx="1080" cy="100" r="3" fill="#fff" opacity="0.3"/>
  <circle cx="1050" cy="120" r="2" fill="#fff" opacity="0.2"/>
  <circle cx="1100" cy="530" r="4" fill="#fff" opacity="0.25"/>
  <circle cx="100" cy="540" r="2" fill="#fff" opacity="0.2"/>
</svg>`;

async function main() {
  // Generate OG image
  const ogBuffer = await sharp(Buffer.from(OG_SVG)).png().toBuffer();
  writeFileSync(join(publicDir, 'og-image.png'), ogBuffer);
  console.log('Created public/og-image.png');

  // Generate Apple Touch Icon from shield SVG
  const iconBuffer = await sharp(Buffer.from(SHIELD_SVG)).resize(180, 180).png().toBuffer();
  writeFileSync(join(publicDir, 'apple-touch-icon.png'), iconBuffer);
  console.log('Created public/apple-touch-icon.png');

  console.log('All assets generated successfully.');
}

main().catch(console.error);
