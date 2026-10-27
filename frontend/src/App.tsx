import Library, { type Media } from './Library'
import { useEffect, useState } from 'react'
import { ArrowRight, BookOpen, Check, ChevronDown, Clapperboard, Compass, Database, Film, Heart, LayoutDashboard, Menu, Plus, Search, Settings2, ShieldCheck, Sparkles, Tv, UploadCloud, X } from 'lucide-react'

type Dashboard = { total: number; movies: number; series: number; anime: number; owned: number; missing: number }
const initial: Dashboard = { total: 0, movies: 0, series: 0, anime: 0, owned: 0, missing: 0 }
const nav = [
  { title: 'Übersicht', icon: LayoutDashboard },
  { title: 'Entdecken', icon: Compass },
  { title: 'Meine Sammlung', icon: Clapperboard },
  { title: 'Wunschliste', icon: Heart },
]
const comingSoon = ['Einstellungen']

export default function App() {
  const [page, setPage] = useState('Übersicht')
  const [mobile, setMobile] = useState(false)
  const [stats, setStats] = useState<Dashboard>(initial)
  const [media, setMedia] = useState<Media[]>([])
  const [online, setOnline] = useState<boolean | null>(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('Alle')

  const refresh = async () => {
      try {
        const [health, dashboard, items] = await Promise.all([
          fetch('/api/health'), fetch('/api/dashboard'), fetch('/api/media'),
        ])
        if (!health.ok || !dashboard.ok || !items.ok) throw new Error('API unavailable')
        const [summary, list] = await Promise.all([dashboard.json() as Promise<Dashboard>, items.json() as Promise<Media[]>])
        setStats(summary); setMedia(list); setOnline(true)
      } catch { setOnline(false) }
    }

  useEffect(() => {
    void refresh()
    const timer = setInterval(() => { void refresh() }, 30000)
    return () => { clearInterval(timer) }
  }, [])

  const filtered = media.filter(item => {
    const matchesName = item.title.toLocaleLowerCase('de').includes(query.toLocaleLowerCase('de'))
    const matchesCategory = category === 'Alle' || item.kind === ({ Filme: 'movie', Serien: 'series', Anime: 'anime' } as Record<string, string>)[category]
    return matchesName && matchesCategory
  })

  const navigate = (name: string) => { setPage(name); setMobile(false) }
  return <div className="app">
    {mobile && <button className="scrim" onClick={() => setMobile(false)} aria-label="Menü schließen" />}
    <aside className={`sidebar ${mobile ? 'is-open' : ''}`}>
      <div className="brand">
        <img src="/assets/Cinearis.png" alt="" className="brand-logo" />
        <div><strong>CINEARIS</strong><small>NOVARION ECOSYSTEM</small></div>
        <button className="mobile-close" onClick={() => setMobile(false)} aria-label="Menü schließen"><X size={20}/></button>
      </div>
      <p className="side-label">WORKSPACE</p>
      <nav aria-label="Hauptnavigation">
        {nav.map(({ title, icon: Icon }) => <button key={title} className={`nav-link ${page === title ? 'selected' : ''}`} onClick={() => navigate(title)}><Icon size={18} strokeWidth={1.8}/>{title}{title === 'Wunschliste' && <span className="nav-count">{media.filter(m => m.status === 'wishlist').length}</span>}</button>)}
      </nav>
      <p className="side-label side-label2">SYSTEM</p>
      <nav aria-label="Systemnavigation">
        <button className={`nav-link ${page === 'Einstellungen' ? 'selected' : ''}`} onClick={() => navigate('Einstellungen')}><Settings2 size={18}/>Einstellungen</button>
      </nav>
      <div className="side-bottom">
        <div className="system-card"><span className="system-icon"><ShieldCheck size={18}/></span><div><strong>Systemstatus</strong><small>{online === null ? 'Verbindung wird geprüft' : online ? 'Alle Systeme online' : 'Backend nicht erreichbar'}</small></div><span className={`status-dot ${online ? 'ok' : online === false ? 'bad' : ''}`}/></div>
        <div className="side-version"><span>Cinearis</span><span>v0.4.0</span></div>
      </div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div className="breadcrumbs"><button className="menu-toggle" onClick={() => setMobile(true)} aria-label="Menü öffnen"><Menu size={21}/></button><span>Workspace</span><span className="slash">/</span><strong>{page}</strong></div>
        <div className="top-actions"><span className="phase-badge"><span className="phase-dot"/> PHASE 04 · COLLECTION</span><div className="avatar">C</div></div>
      </header>
      <div className="content">
        <div className="intro"><div><div className="eyebrow"><Sparkles size={14}/> YOUR PERSONAL MEDIA UNIVERSE</div><h1>{page === 'Übersicht' ? <>Willkommen bei <span>Cinearis.</span></> : page + '.'}</h1><p>{page === 'Übersicht' ? 'Entdecke, sammle und organisiere Filme, Serien und Anime – alles an einem Ort.' : 'Dein zentraler Ort für Entdeckungen und Mediensammlungen.'}</p></div><button className="outline-btn" onClick={() => navigate('Meine Sammlung')}><BookOpen size={16}/> Sammlung ansehen <ArrowRight size={16}/></button></div>
        {online === false && <div className="warning">Das Backend ist aktuell nicht erreichbar. Prüfe die Docker-Container und die Datenbankverbindung.</div>}
        {comingSoon.includes(page) ? <section className="coming"><span className="coming-icon"><Sparkles size={26}/></span><h2>Hier entsteht etwas Neues.</h2><p>Dieser Bereich ist für eine kommende Cinearis-Version vorgesehen. In v0.1.0 konzentrieren wir uns auf das stabile Fundament.</p><button className="primary-btn" onClick={() => navigate('Übersicht')}>Zur Übersicht <ArrowRight size={16}/></button></section> : <>
          {(page === 'Entdecken' || page === 'Meine Sammlung' || page === 'Wunschliste') ? <Library page={page} items={media} onRefresh={refresh}/> : <>
          <section className="hero">
            <div className="hero-copy"><div className="hero-tag"><span className="pulse"/> DIE REISE BEGINNT</div><h2>Jede große Sammlung<br/>beginnt mit einer <em>Entdeckung.</em></h2><p>Dein persönlicher Ort für alles, was du sehen möchtest. Du kannst bereits jetzt Medien suchen, hinzufügen und deinen Sehfortschritt verwalten.</p><button className="primary-btn" onClick={() => navigate('Entdecken')}>Cinearis entdecken <ArrowRight size={17}/></button></div>
            <div className="hero-art"><div className="orb orb1"/><div className="orb orb2"/><div className="art-ring"/><img src="/assets/Cinearis.png" alt="Cinearis Logo" /></div>
          </section>
          <div className="section-line"><h3>Deine Mediathek <span>im Überblick</span></h3><span>LIVE-DATEN</span></div>
          <div className="stats-grid">
            {[
              { name: 'Gesamte Titel', value: stats.total, icon: Database, tint: 'blue', detail: 'In deiner Sammlung' },
              { name: 'Filme', value: stats.movies, icon: Film, tint: 'purple', detail: 'Entdeckte Filme' },
              { name: 'Serien', value: stats.series, icon: Tv, tint: 'pink', detail: 'Entdeckte Serien' },
              { name: 'Anime', value: stats.anime, icon: Sparkles, tint: 'cyan', detail: 'Entdeckte Anime' },
            ].map(({ name, value, icon: Icon, tint, detail }) => <div className="stat" key={name}><div className="stat-top"><span>{name}</span><span className={`stat-icon ${tint}`}><Icon size={19}/></span></div><strong>{value.toLocaleString('de-DE')}</strong><small>{detail}</small></div>)}
          </div>
          <div className="lower-grid">
            <section className="panel collection"><div className="panel-heading"><div><h3>Deine Sammlung</h3><p>Alle bisher erfassten Titel auf einen Blick.</p></div><span className="panel-count">{stats.total} Titel</span></div>
              <div className="filter-row"><div className="filter-tabs">{['Alle','Filme','Serien','Anime'].map(c => <button key={c} className={category === c ? 'active' : ''} onClick={() => setCategory(c)}>{c}</button>)}</div><label className="search-box"><Search size={17}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Suchen ..." aria-label="Sammlung durchsuchen"/></label></div>
              {filtered.length ? <div className="media-list">{filtered.map(item => <div className="media-row" key={item.id}><span className="media-mark"><Clapperboard size={18}/></span><div><strong>{item.title}</strong><small>{item.kind}</small></div><span className="media-status">{item.status}</span></div>)}</div> : <div className="empty"><div className="empty-symbol"><Clapperboard size={33}/></div><h4>{query || category !== 'Alle' ? 'Keine passenden Titel' : 'Deine Sammlung wartet auf dich.'}</h4><p>{query || category !== 'Alle' ? 'Passe deine Suche oder den Filter an.' : 'Füge Titel über „Entdecken“ hinzu, damit sie hier erscheinen.'}</p><span className="soon-label">JETZT MEDIEN HINZUFÜGEN</span></div>}</section>
            <section className="panel quick"><div className="panel-heading"><div><h3>Demnächst</h3><p>Die nächsten Cinearis-Meilensteine.</p></div><ChevronDown size={18}/></div>
              <div className="milestones"><div className="milestone current"><span className="milestone-icon"><Check size={18}/></span><div><strong>Phase 1 · Fundament</strong><small>Dashboard, API & Docker</small></div><span className="mini-pill">JETZT</span></div><div className="milestone"><span className="milestone-icon"><UploadCloud size={19}/></span><div><strong>Phase 2 · KI-Erkennung</strong><small>Bildanalyse mit OCR & Vision</small></div></div><div className="milestone"><span className="milestone-icon"><Search size={18}/></span><div><strong>Phase 3 · Metadaten</strong><small>TMDB & AniList verbinden</small></div></div><div className="milestone"><span className="milestone-icon"><Plus size={18}/></span><div><strong>Phase 4 · Erweiterte Watchlist</strong><small>Titel speichern & verwalten</small></div></div></div>
              <div className="quick-footer"><span><span className="tiny-dot"/> Mit Novarion verbunden</span><span>v0.4.0</span></div>
            </section>
          </div>
          </>}
        </>}
        <footer>© Cinearis · Part of the Novarion Ecosystem <span>Crafted for your next discovery ✦</span></footer>
      </div>
    </main>
  </div>
}
