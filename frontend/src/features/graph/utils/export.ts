export function exportSVG(svgEl: SVGSVGElement, filename = 'evidence-graph.svg'): void {
  const clone = svgEl.cloneNode(true) as SVGSVGElement;
    const styles = getComputedStyles();
  const styleTag = document.createElementNS('http://www.w3.org/2000/svg', 'style');
  styleTag.textContent = styles;
  clone.insertBefore(styleTag, clone.firstChild);

  const serializer = new XMLSerializer();
  const source = serializer.serializeToString(clone);
  const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
  downloadBlob(blob, filename);
}

export function exportPNG(svgEl: SVGSVGElement, filename = 'evidence-graph.png'): Promise<void> {
  return new Promise((resolve, reject) => {
    const clone = svgEl.cloneNode(true) as SVGSVGElement;
    const styles = getComputedStyles();
  const styleTag = document.createElementNS('http://www.w3.org/2000/svg', 'style');
    styleTag.textContent = styles;
    clone.insertBefore(styleTag, clone.firstChild);

    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(clone);

    const canvas = document.createElement('canvas');
    const rect = svgEl.getBoundingClientRect();
    const scale = 2;
    canvas.width = rect.width * scale;
    canvas.height = rect.height * scale;
    const ctx = canvas.getContext('2d');
    if (!ctx) { reject(new Error('Canvas context not available')); return; }

    const img = new Image();
    const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    img.onload = () => {
      ctx.scale(scale, scale);
      ctx.fillStyle = '#09090b';
      ctx.fillRect(0, 0, rect.width, rect.height);
      ctx.drawImage(img, 0, 0, rect.width, rect.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((b) => {
        if (b) {
          downloadBlob(b, filename);
          resolve();
        } else {
          reject(new Error('Failed to create PNG blob'));
        }
      }, 'image/png');
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load SVG for PNG export'));
    };

    img.src = url;
  });
}

function getComputedStyles(): string {
  const sheets = document.styleSheets;
  let css = '';
  for (let i = 0; i < sheets.length; i++) {
    try {
      const sheet = sheets[i];
      if (sheet.cssRules) {
        for (let j = 0; j < sheet.cssRules.length; j++) {
          css += sheet.cssRules[j].cssText + '\n';
        }
      }
    } catch {
      // skip cross-origin sheets
    }
  }
  return css;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
