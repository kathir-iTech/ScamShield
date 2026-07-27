export function AnimatedBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="absolute inset-0 bg-[#08080c]" />
      <div
        className="absolute -left-[10%] -top-[10%] h-[50%] w-[50%] animate-ambient-float opacity-30"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(10,132,255,0.15) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute -bottom-[10%] -right-[10%] h-[60%] w-[60%] animate-ambient-float-2 opacity-25"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(90,200,250,0.12) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute left-[40%] top-[30%] h-[40%] w-[40%] animate-pulse-glow opacity-20"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(175,82,222,0.1) 0%, transparent 70%)',
        }}
      />
      <div className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
        }}
      />
    </div>
  );
}
