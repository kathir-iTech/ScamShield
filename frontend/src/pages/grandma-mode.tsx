import { useRef, useState, useCallback, useEffect } from 'react';
import { PageTransition } from '@/components/ui/page-transition';
import { analyzeText } from '@/services/scamshield';
import tacticExplain from '@/lib/scamshield/tactic-explainers.json' with { type: 'json' };
import { Volume2, VolumeX, Mic, Volume2 as Speak, ArrowLeft, Trash2, Check } from 'lucide-react';

interface VoiceInfo {
  name: string;
  lang: string;
  isTamil: boolean;
}

// Build a plain-language explanation to speak aloud, reusing the tactic
// explainer text so Grandma Mode says the same things the app already teaches.
function buildSpokenText(
  result: { risk_level: string; detected_indicators: string[] }
): string {
  const level = (result.risk_level || '').toLowerCase();

  const indicatorTexts: string[] = [];
  for (const ind of result.detected_indicators || []) {
    const entry = (tacticExplain as Record<string, { tactic: string; explainer: string }>)[ind];
    if (entry) indicatorTexts.push(entry.explainer);
  }

  let opening: string;
  if (level === 'critical' || level === 'high') {
    opening = 'This message looks like a scam. Be very careful, and do not share any password, code, or money.';
  } else if (level === 'medium' || level === 'low') {
    opening = 'This message has some suspicious signs. Take a moment before you act, and do not share codes or passwords.';
  } else {
    opening = 'This message does not look dangerous. There are no strong warning signs here.';
  }

  const body = indicatorTexts.length > 0
    ? 'Here is what they are trying to do. ' + indicatorTexts.join(' ')
    : '';

  const ending = 'If you are not sure, ask a family member you trust before you reply, or call the official number on the back of your bank card. Never share your one-time password with anyone.';

  return [opening, body, ending].filter(Boolean).join(' ');
}

function isTamilLang(lang: string): boolean {
  return /^ta([-_]|$)/i.test(lang || '');
}

export default function GrandmaMode() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<{ risk_level: string; detected_indicators: string[] } | null>(null);
  const [spoken, setSpoken] = useState('');
  const [voices, setVoices] = useState<VoiceInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [tamilVoiceAvailable, setTamilVoiceAvailable] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replayedFinished, setReplayedFinished] = useState(false);
  const cancelledRef = useRef(false);

  // Load available voices and honestly report what exists (incl. Tamil).
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setSpeechSupported(false);
      return;
    }
    const loadVoices = () => {
      const list = window.speechSynthesis.getVoices();
      setVoices(
        list.map((v) => ({ name: v.name, lang: v.lang || '', isTamil: isTamilLang(v.lang) }))
      );
      setTamilVoiceAvailable(list.some((v) => isTamilLang(v.lang)));
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  const stopSpeaking = useCallback(() => {
    cancelledRef.current = true;
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }, []);

  const speak = useCallback((content: string) => {
    if (!('speechSynthesis' in window)) {
      setError('This browser does not support speech. You can still read the result below.');
      return;
    }
    cancelledRef.current = false;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(content);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    const found = window.speechSynthesis.getVoices();
    // Prefer an English (en-IN) voice if available; otherwise any English voice.
    const enVoice = found.find((v) => /^en(-|_)?in$/i.test(v.lang))
      || found.find((v) => /^en/i.test(v.lang))
      || found[0];
    if (enVoice) utterance.voice = enVoice;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => { setSpeaking(false); setReplayedFinished(true); };
    utterance.onerror = () => { setSpeaking(false); };
    window.speechSynthesis.speak(utterance);
  }, []);

  const handleAnalyse = async () => {
    if (!text.trim()) return;
    setError(null);
    setLoading(true);
    setReplayedFinished(false);
    try {
      const res = await analyzeText(text);
      const mini = { risk_level: res.risk_level, detected_indicators: res.detected_indicators };
      setResult(mini);
      const content = buildSpokenText(mini);
      setSpoken(content);
      speak(content);
    } catch (e) {
      setError((e as Error).message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-6 py-10 sm:py-14">
        {/* Simplified header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-3xl glass">
            <Volume2 className="h-8 w-8 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Grandma Mode</h1>
          <p className="mt-3 text-lg text-text-secondary/80">One big button. We read the answer out loud.</p>
          <p className="mt-1 text-sm text-text-tertiary">Everything stays on your device — nothing is sent anywhere.</p>
        </div>

        {/* Speech / voice availability note */}
        <div className="mb-6 glass rounded-2xl p-4 text-left animate-slide-up">
          {speechSupported ? (
            <p className="text-xs text-text-tertiary">
              Voice available in this browser: {voices.length > 0 ? voices.slice(0, 3).map((v) => v.name).join(', ') : 'loading voices…'}
              {' '}{tamilVoiceAvailable ? '(Tamil voice available)' : '(no Tamil voice detected on this device)'}
            </p>
          ) : (
            <p className="text-xs text-warning">This browser does not support text-to-speech. You can still read the result below.</p>
          )}
        </div>

        {/* Message input */}
        <div className="glass rounded-2xl overflow-hidden">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            placeholder="Type or paste the message here…"
            className="w-full resize-none bg-transparent px-5 py-4 text-base text-text-primary placeholder:text-text-tertiary focus:outline-none"
            aria-label="Message to check"
          />
          <div className="flex items-center justify-between border-t border-glass-border px-4 py-3">
            <button
              onClick={() => { setText(''); setResult(null); setSpoken(''); stopSpeaking(); }}
              disabled={!text && !result}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-xs text-text-tertiary hover:text-text-secondary disabled:opacity-30"
              aria-label="Clear"
            >
              <Trash2 className="h-4 w-4" /> Clear
            </button>
            <button
              onClick={handleAnalyse}
              disabled={!text.trim() || loading}
              className="glass-button relative inline-flex h-14 items-center gap-2.5 rounded-2xl px-8 text-lg font-bold text-white disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Mic className="h-5 w-5" />
              {loading ? 'Checking…' : 'Check a message'}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 glass rounded-2xl p-4 text-sm text-danger" role="alert">{error}</div>
        )}

        {/* Result */}
        {result && (
          <div className="mt-6 space-y-4 animate-scale-in">
            <div className="glass rounded-2xl p-6">
              <p className="text-sm font-semibold text-text-primary">
                {result.risk_level === 'CRITICAL' || result.risk_level === 'HIGH'
                  ? 'This looks like a scam.'
                  : result.risk_level === 'MEDIUM' || result.risk_level === 'LOW'
                  ? 'Be careful — some signs here.'
                  : 'This looks okay.'}
              </p>
              <p className="mt-2 text-base leading-relaxed text-text-secondary">{spoken}</p>

              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  onClick={() => speak(spoken)}
                  disabled={!speechSupported || speaking}
                  className="inline-flex h-11 items-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white hover:bg-accent/90 disabled:opacity-40"
                >
                  {speaking ? <VolumeX className="h-4 w-4" /> : <Speak className="h-4 w-4" />}
                  {speaking ? 'Speaking…' : 'Read again'}
                </button>
                {speaking && (
                  <button
                    onClick={stopSpeaking}
                    className="inline-flex h-11 items-center gap-2 rounded-xl border border-glass-border bg-glass px-5 text-sm font-medium text-text-secondary hover:text-text-primary"
                  >
                    <VolumeX className="h-4 w-4" /> Stop
                  </button>
                )}
              </div>
            </div>

            {replayedFinished && (
              <div className="flex items-center gap-2 text-sm text-success">
                <Check className="h-4 w-4" />
                Finished reading. Want to hear it again?
              </div>
            )}

            <button
              onClick={() => { setResult(null); setSpoken(''); setText(''); stopSpeaking(); }}
              className="w-full rounded-2xl border border-glass-border bg-glass py-3 text-sm font-medium text-text-secondary hover:text-text-primary"
            >
              Check another message
            </button>
          </div>
        )}

        <div className="mt-8 text-center">
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm text-text-tertiary hover:text-text-secondary"
          >
            <ArrowLeft className="h-4 w-4" /> Back
          </button>
        </div>
      </div>
    </PageTransition>
  );
}
