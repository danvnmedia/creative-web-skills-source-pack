import { useEffect, useState } from 'react';
import { ArrowDownRight, ArrowRight, ArrowUpRight, Compass } from 'lucide-react';

type Expedition = {
  number: string;
  name: string;
  region: string;
  duration: string;
  description: string;
  tone: string;
  image: string;
};

const expeditions: Expedition[] = [
  { number: '01', name: 'The quiet coast', region: 'Atlantic / 42.7° N', duration: '7 day field note', description: 'Salt on the windows. Low light on the headland. An invitation to keep walking after the road ends.', tone: 'coast', image: 'coast.webp' },
  { number: '02', name: 'Blue hour, inland', region: 'Highlands / 57.2° N', duration: '4 day field note', description: 'A route drawn by ridgelines and changing weather, with enough room for the unexpected.', tone: 'highland', image: 'highland.webp' },
  { number: '03', name: 'The last light', region: 'Desert / 24.6° N', duration: '6 day field note', description: 'Follow a long shadow into a quieter landscape. Stay for the stars and the conversations between them.', tone: 'desert', image: 'desert.webp' },
];

const asset = (name: string) => `${import.meta.env.BASE_URL}assets/${name}`;

export default function App() {
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [phase, setPhase] = useState<'day' | 'night'>('day');
  const [active, setActive] = useState(0);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReducedMotion(query.matches);
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);

  const changeScene = (next: 'day' | 'night') => {
    if (next === phase) return;
    const update = () => setPhase(next);
    if (!reducedMotion && 'startViewTransition' in document) document.startViewTransition(update);
    else update();
  };

  return (
    <main className={`site-shell phase-${phase}`}>
      <section className="hero" id="top" aria-labelledby="hero-title">
        <div className="hero-art" aria-hidden="true">
          <img className="hero-photo" src={asset("coast.webp")} alt="" fetchPriority="high" />
          <div className="hero-grain" />
          <div className="hero-orbit" />
        </div>
        <header className="topbar">
          <a className="wordmark" href="#top" aria-label="Asme, back to top"><Compass size={24} strokeWidth={1.4} aria-hidden="true" /><span>asme<span className="wordmark-dot">.</span></span></a>
          <nav aria-label="Primary navigation"><a href="#atlas">The atlas</a><a href="#approach">Our approach</a></nav>
          <a className="header-action" href="../" aria-label="Back to showcase index">All studies <ArrowUpRight size={16} aria-hidden="true" /></a>
        </header>

        <div className="hero-content">
          <div className="hero-overline"><span className="overline-rule" /> FIELD NOTES / VOL. 01 <span className="overline-right">AN OPEN INVITATION</span></div>
          <h1 id="hero-title">Go where<br /><em>wonder</em> leads.</h1>
          <div className="hero-bottom">
            <p>Small journeys for people who would rather feel a place than collect one. Choose a direction. We will leave room for discovery.</p>
            <a className="round-link" href="#atlas" aria-label="Explore the atlas"><ArrowDownRight size={29} strokeWidth={1.35} aria-hidden="true" /></a>
          </div>
        </div>
        <div className="hero-coordinate" aria-hidden="true">AS / 001 — 09:24 UTC</div>
      </section>

      <section className="atlas" id="atlas" aria-labelledby="atlas-title">
        <div className="section-head"><span>01 / THE ATLAS</span><span>THREE DIRECTIONS, NO FIXED ROUTE</span></div>
        <div className="atlas-intro"><h2 id="atlas-title">Find your<br /><em>somewhere.</em></h2><p>Consider this a beginning. Each field note is a fictional concept journey, made to show how a place can become an interface.</p></div>
        <div className="expeditions" role="group" aria-label="Choose a field note">
          {expeditions.map((expedition, index) => (
            <button className={`expedition ${expedition.tone} ${active === index ? 'is-active' : ''}`} key={expedition.number} type="button" aria-pressed={active === index} onClick={() => setActive(index)}>
              <span className="expedition-landscape" aria-hidden="true"><img src={asset(expedition.image)} alt="" loading="lazy" /></span>
              <span className="expedition-top"><span>FIELD NOTE {expedition.number}</span><ArrowUpRight size={18} strokeWidth={1.4} aria-hidden="true" /></span>
              <span className="expedition-bottom"><strong>{expedition.name}</strong><small>{expedition.region}</small></span>
            </button>
          ))}
        </div>
        <div className="selection" aria-live="polite"><span>SELECTED / {expeditions[active].number}</span><p>{expeditions[active].description}</p><span>{expeditions[active].duration}</span></div>
      </section>

      <section className="approach" id="approach" aria-labelledby="approach-title">
        <img className="approach-photo" src={asset("highland.webp")} alt="" loading="lazy" aria-hidden="true" />
        <div className="section-head"><span>02 / THE APPROACH</span><span>TRAVEL AT HUMAN SPEED</span></div>
        <div className="approach-layout"><p className="approach-kicker">The good part is often<br />between the destinations.</p><h2 id="approach-title">Leave space<br />for <em>elsewhere.</em></h2></div>
        <div className="approach-bottom"><p>Asme is a design concept for curious travel: thoughtful routes, tactile stories, and moments that are yours to notice.</p><div className="scene-switch" role="group" aria-label="Change the atmosphere"><button type="button" aria-pressed={phase === 'day'} onClick={() => changeScene('day')}>Daylight</button><button type="button" aria-pressed={phase === 'night'} onClick={() => changeScene('night')}>After dark</button></div></div>
      </section>

      <footer className="footer"><a href="#top" className="footer-wordmark">asme<span>.</span></a><p>AN ORIGINAL INTERACTIVE FIELD STUDY / 2026</p><a href="#top">Back to the beginning <ArrowRight size={15} aria-hidden="true" /></a><small>Motion study / Staggered hero reveal, transform based card feedback, scroll linked section entry, and a same document View Transition for atmosphere. Reduced motion keeps all content still.</small></footer>
    </main>
  );
}
