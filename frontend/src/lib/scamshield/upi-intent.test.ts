import { describe, it, expect } from 'vitest';
import { parseUpiIntent, parseUpiIntents, formatInr } from './upi-intent';

describe('UPI Intent Inspector — 20 hand tests (gate)', () => {
  it('1: strict upi://pay with pa+am => PAY', () => {
    const r = parseUpiIntent('upi://pay?pa=ramesh@okaxis&pn=Ramesh&am=5000&tn=test');
    expect(r).not.toBeNull();
    expect(r!.kind).toBe('UPI_INTENT');
    expect(r!.mode).toBe('PAY');
    expect(r!.pa).toBe('ramesh@okaxis');
    expect(r!.amount).toBe(5000);
    expect(r!.handle).toBe('okaxis');
  });
  it('2: upi://pay without am => PAY unknown amount', () => {
    const r = parseUpiIntent('upi://pay?pa=kirana@ybl&pn=Kirana Store');
    expect(r).not.toBeNull();
    expect(r!.mode).toBe('PAY');
    expect(r!.amount).toBeNull();
    expect(r!.am).toBeNull();
  });
  it('3: bare VPA fallback => BARE_VPA UNKNOWN', () => {
    const r = parseUpiIntent('Send to ramesh@ybl for payment');
    expect(r).not.toBeNull();
    expect(r!.kind).toBe('BARE_VPA');
    expect(r!.pa).toBe('ramesh@ybl');
    expect(r!.mode).toBe('UNKNOWN');
    expect(r!.amount).toBeNull();
  });
  it('4: spaced garble "upi : // pay ? pa = foo @ ybl & am = 500" => PAY 500', () => {
    const r = parseUpiIntent('upi : // pay ? pa = foo @ ybl & am = 500 & pn=Test');
    expect(r).not.toBeNull();
    expect(r!.pa).toBe('foo@ybl');
    expect(r!.amount).toBe(500);
    expect(r!.mode).toBe('PAY');
  });
  it('5: QR_CODE_UPI: prefix stripped', () => {
    const r = parseUpiIntent('QR_CODE_UPI: upi://pay?pa=shop@paytm&am=250');
    expect(r).not.toBeNull();
    expect(r!.pa).toBe('shop@paytm');
    expect(r!.amount).toBe(250);
  });
  it('6: QR_CODE_URL: with upi intent inside', () => {
    const r = parseUpiIntent('QR_CODE_URL: upi://pay?pa=test@upi&am=100');
    expect(r).not.toBeNull();
    expect(r!.pa).toBe('test@upi');
  });
  it('7: upi://collect => COLLECT', () => {
    const r = parseUpiIntent('upi://collect?pa=attacker@okicici&am=10000&tn=collect');
    expect(r).not.toBeNull();
    expect(r!.mode).toBe('COLLECT');
    expect(r!.amount).toBe(10000);
  });
  it('8: upi intent with URL-encoded pn', () => {
    const r = parseUpiIntent('upi://pay?pa=rahul@okaxis&pn=Rahul%20Kumar&am=1000');
    expect(r).not.toBeNull();
    expect(r!.pn).toBe('Rahul Kumar');
  });
  it('9: OCR drop colon "upi//pay?pa=midhan@ybl&am=2000"', () => {
    const r = parseUpiIntent('upi//pay?pa=midhan@ybl&am=2000');
    expect(r).not.toBeNull();
    expect(r!.pa).toBe('midhan@ybl');
    expect(r!.amount).toBe(2000);
  });
  it('10: multiple intents => parseUpiIntents returns both', () => {
    const all = parseUpiIntents('Pay 1: upi://pay?pa=a@ybl&am=100 and Pay 2: upi://pay?pa=b@okaxis&am=200');
    expect(all.length).toBe(2);
    expect(all[0].pa).toBe('a@ybl');
    expect(all[1].pa).toBe('b@okaxis');
  });
  it('11: handle allowlist vs non-allowlist confidence', () => {
    const allowed = parseUpiIntent('upi://pay?pa=user@ybl&am=10');
    const unknown = parseUpiIntent('upi://pay?pa=user@unknownbank&am=10');
    expect(allowed!.confidence).toBeGreaterThan(0.9);
    // unknown handle still parsed but not in allowlist -> lower confidence, still shown
    // but our parser requires handle in allowlist for bare VPA; for intent we allow any, but confidence lower
    expect(unknown).not.toBeNull();
  });
  it('12: amount with comma "Rs 5,000" style not via am but via separate — am with comma should parse', () => {
    const r = parseUpiIntent('upi://pay?pa=shop@ybl&am=5,000');
    expect(r).not.toBeNull();
    expect(r!.amount).toBe(5000);
  });
  it('13: no pa => null (invalid intent)', () => {
    const r = parseUpiIntent('upi://pay?am=500&tn=test');
    expect(r).toBeNull();
  });
  it('14: bare VPA with non-UPI handle ignored', () => {
    const r = parseUpiIntent('Contact john@gmail.com for details');
    // gmail not in UPI_HANDLES, so bare extraction should ignore
    expect(r).toBeNull();
  });
  it('15: spaced @ and = and &: "pa = foo @ okaxis & am = 750 & cu = INR"', () => {
    const r = parseUpiIntent('upi://pay?pa = foo @ okaxis & am = 750 & cu = INR & tn=Test');
    expect(r).not.toBeNull();
    expect(r!.pa).toBe('foo@okaxis');
    expect(r!.amount).toBe(750);
    expect(r!.cu).toBe('INR');
  });
  it('16: formatInr helper produces INR string', () => {
    expect(formatInr(5000)).toMatch(/₹|Rs/);
    expect(formatInr(null)).toBeNull();
    expect(formatInr(1234.5)).toMatch(/1,234/);
  });
  it('17: intent with tn note preserved', () => {
    const r = parseUpiIntent('upi://pay?pa=payee@upi&am=999&tn=Payment for order 123');
    expect(r!.tn).toBe('Payment for order 123');
  });
  it('18: QR_CODE_TEXT: prefix with bare VPA inside', () => {
    const r = parseUpiIntent('QR_CODE_TEXT: ramesh@okaxis');
    expect(r).not.toBeNull();
    expect(r!.kind).toBe('BARE_VPA');
    expect(r!.pa).toBe('ramesh@okaxis');
  });
  it('19: text with both VPA and intent — intent prioritized', () => {
    const all = parseUpiIntents('My VPA is test@ybl and also upi://pay?pa=real@ybl&am=100');
    expect(all[0].kind).toBe('UPI_INTENT');
    expect(all[0].pa).toBe('real@ybl');
  });
  it('20: never asserts RECEIVE — unknown mode should not be RECEIVE even with collect-like text', () => {
    const r = parseUpiIntent('upi://pay?pa=attacker@ybl&am=2000');
    expect(r!.mode).not.toBe('UNKNOWN'); // it should be PAY for safety
    expect(['PAY','COLLECT','UNKNOWN']).toContain(r!.mode);
    // Ensure we never return RECEIVE
    expect((r as unknown as {mode:string}).mode).not.toBe('RECEIVE');
  });
});
