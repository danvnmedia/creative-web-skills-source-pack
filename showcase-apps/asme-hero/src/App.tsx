import { FormEvent, useEffect, useRef, useState } from 'react';
import { ArrowRight, Globe, Instagram, Twitter } from 'lucide-react';

const VIDEO_URL = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_115001_bcdaa3b4-03de-47e7-ad63-ae3e392c32d4.mp4';

function useLoopingVideoFade() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const frameRef = useRef<number>();
  const resetTimerRef = useRef<number>();
  const opacityRef = useRef(0);
  const fadingOutRef = useRef(false);
  const reducedMotionRef = useRef(window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  const fadeTo = (target: number, duration = 500) => {
    if (frameRef.current) cancelAnimationFrame(frameRef.current);
    const video = videoRef.current;
    if (!video) return;

    const initial = opacityRef.current;
    const startedAt = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = progress * progress * (3 - 2 * progress);
      const opacity = initial + (target - initial) * eased;
      opacityRef.current = opacity;
      video.style.opacity = String(opacity);
      if (progress < 1) frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
  };

  const handleLoadedData = () => {
    if (reducedMotionRef.current) {
      const video = videoRef.current;
      if (!video) return;
      video.pause();
      opacityRef.current = 1;
      video.style.opacity = '1';
      return;
    }
    fadingOutRef.current = false;
    void videoRef.current?.play().catch(() => undefined);
    fadeTo(1);
  };

  const handleTimeUpdate = () => {
    if (reducedMotionRef.current) return;
    const video = videoRef.current;
    if (!video || !Number.isFinite(video.duration)) return;
    if (video.duration - video.currentTime <= 0.55 && !fadingOutRef.current) {
      fadingOutRef.current = true;
      fadeTo(0);
    }
  };

  const handleEnded = () => {
    if (reducedMotionRef.current) return;
    const video = videoRef.current;
    if (!video) return;
    if (frameRef.current) cancelAnimationFrame(frameRef.current);
    opacityRef.current = 0;
    video.style.opacity = '0';
    resetTimerRef.current = window.setTimeout(() => {
      video.currentTime = 0;
      fadingOutRef.current = false;
      void video.play().then(() => fadeTo(1)).catch(() => undefined);
    }, 100);
  };

  useEffect(() => {
    const resumeWhenVisible = () => {
      const video = videoRef.current;
      if (document.hidden || !video || reducedMotionRef.current) return;
      if (video.paused) void video.play().catch(() => undefined);
      if (!fadingOutRef.current && opacityRef.current < 1) fadeTo(1);
    };
    document.addEventListener('visibilitychange', resumeWhenVisible);
    return () => {
      document.removeEventListener('visibilitychange', resumeWhenVisible);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      if (resetTimerRef.current) window.clearTimeout(resetTimerRef.current);
    };
  }, []);

  return { videoRef, handleLoadedData, handleTimeUpdate, handleEnded };
}

export default function App() {
  const { videoRef, handleLoadedData, handleTimeUpdate, handleEnded } = useLoopingVideoFade();
  const [subscribed, setSubscribed] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubscribed(true);
  };

  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden bg-black text-white">
      <video
        ref={videoRef}
        className="absolute inset-0 h-full w-full translate-y-[17%] object-cover"
        src={VIDEO_URL}
        muted
        autoPlay
        playsInline
        preload="auto"
        onLoadedData={handleLoadedData}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        style={{ opacity: 0 }}
        aria-hidden="true"
      />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,.72)_0%,rgba(0,0,0,.08)_35%,rgba(0,0,0,.28)_100%)]" />

      <nav className="relative z-20 px-6 py-6" aria-label="Primary navigation">
        <div className="liquid-glass mx-auto flex max-w-5xl items-center justify-between rounded-full px-6 py-3">
          <div className="relative z-10 flex items-center gap-8">
            <a href="#" className="flex items-center gap-2 text-lg font-semibold text-white" aria-label="Asme home">
              <Globe size={24} aria-hidden="true" />
              <span>Asme</span>
            </a>
            <div className="hidden items-center gap-8 md:flex">
              {['Features', 'Pricing', 'About'].map((item) => (
                <a key={item} href={`#${item.toLowerCase()}`} className="text-sm font-medium text-white/80 transition-colors hover:text-white">{item}</a>
              ))}
            </div>
          </div>
          <div className="relative z-10 flex items-center gap-4">
            <button type="button" className="text-sm font-medium text-white">Sign Up</button>
            <button type="button" className="liquid-glass rounded-full px-6 py-2 text-sm font-medium text-white">Login</button>
          </div>
        </div>
      </nav>

      <section className="relative z-10 flex flex-1 -translate-y-[20%] flex-col items-center justify-center px-6 py-12 text-center" aria-labelledby="hero-heading">
        <h1
          id="hero-heading"
          className="mb-8 whitespace-nowrap text-5xl tracking-tight text-white max-[420px]:text-[2.5rem] md:text-6xl lg:text-7xl"
          style={{ fontFamily: "'Instrument Serif', serif" }}
        >
          Built for the <em>curious</em>
        </h1>

        <div className="w-full max-w-xl space-y-4">
          <form className="liquid-glass flex items-center gap-3 rounded-full py-2 pl-6 pr-2" onSubmit={handleSubmit}>
            <input
              type="email"
              required
              className="relative z-10 min-w-0 flex-1 bg-transparent text-base text-white outline-none placeholder:text-white/40"
              placeholder={subscribed ? "You're on the list" : 'Enter your email'}
              aria-label="Email address"
              disabled={subscribed}
            />
            <button className="relative z-10 rounded-full bg-white p-3 text-black" type="submit" aria-label="Subscribe to newsletter">
              <ArrowRight size={20} aria-hidden="true" />
            </button>
          </form>
          <p className="px-4 text-sm leading-relaxed text-white">
            Stay updated with the latest news and insights. Subscribe to our newsletter today and never miss out on exciting updates.
          </p>
          <button type="button" className="liquid-glass rounded-full px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-white/5">
            Read our manifesto
          </button>
          <p className="sr-only" aria-live="polite">{subscribed ? 'Subscription confirmed.' : ''}</p>
        </div>
      </section>

      <footer className="relative z-10 flex justify-center gap-4 pb-12">
        {[
          { label: 'Instagram', Icon: Instagram },
          { label: 'Twitter', Icon: Twitter },
          { label: 'Website', Icon: Globe },
        ].map(({ label, Icon }) => (
          <a key={label} href="#" aria-label={label} className="liquid-glass rounded-full p-4 text-white/80 transition-all hover:bg-white/5 hover:text-white">
            <Icon className="relative z-10" size={20} aria-hidden="true" />
          </a>
        ))}
      </footer>
    </main>
  );
}