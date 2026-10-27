import ImageAnalyzer from './ImageAnalyzer'
import { useEffect, useState } from 'react'
import { Check, Film, Heart, Loader2, Plus, Search, Trash2, Tv, X } from 'lucide-react'

export type Media = {
  id: number; title: string; kind: 'movie' | 'series' | 'anime'; status: string
  watch_state: string; season_number: number | null; episode_number: number | null
  poster_url: string | null; release_year: number | null
}
type Suggestion = { title: string; kind: 'movie' | 'series' | 'anime'; provider?: 'tmdb' | 'anilist'; provider_id?: string; poster_url?: string | null; release_year?: number | null }
type Props = { items: Media[]; onRefresh: () => Promise<void>; page: string }
const categories = [{ value: 'movie', label: 'Film' }, { value: 'series', label: 'Serie' }, { value: 'anime', label: 'Anime' }]
const statusLabels: Record<string, string> = { wishlist: 'Wunschliste', planned: 'Geplant', processing: 'In Bearbeitung', owned: 'Vorhanden', ignored: 'Ignoriert' }
const watchLabels: Record<string, string> = { unwatched: 'Nicht gesehen', completed: 'Komplett gesehen', through_episode: 'Bis zu einer Folge', season_completed: 'Staffel gesehen' }

async function api(path: string, options?: RequestInit) {
  const response = await fetch(path, options)
  if (!response.ok) {
    let detail = 'Die Anfrage ist fehlgeschlagen'
    try { const body = await response.json(); detail = typeof body.detail === 'string' ? body.detail : detail } catch { /* HTTP fallback */ }
    throw new Error(detail)
  }
  if (response.status === 204) return null
  return response.json()
}
const json = (method: string, data: object): RequestInit => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })

export default function Library({ items, onRefresh, page }: Props) {
  const [kind, setKind] = useState<'movie' | 'series' | 'anime'>('movie')
  const [term, setTerm] = useState('')
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')
  const [selected, setSelected] = useState<Media | null>(null)
  const [watch, setWatch] = useState('unwatched')
  const [season, setSeason] = useState('1')
  const [episode, setEpisode] = useState('1')
  const [status, setStatus] = useState('wishlist')

  useEffect(() => {
    if (page !== 'Entdecken') return
    const q = term.trim()
    if (q.length < 2) { setSuggestions([]); setError(''); return }
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      setBusy(true); setError('')
      try {
        const result = await api(`/api/search?kind=${kind}&q=${encodeURIComponent(q)}`, { signal: controller.signal })
        if (!controller.signal.aborted) setSuggestions(result)
      } catch (e) {
        if (!controller.signal.aborted) { setSuggestions([]); setError(e instanceof Error ? e.message : 'Suche fehlgeschlagen') }
      } finally { if (!controller.signal.aborted) setBusy(false) }
    }, 450)
    return () => { clearTimeout(timer); controller.abort() }
  }, [term, kind, page])

  const add = async (suggestion: Suggestion) => {
    setNotice(''); setError('')
    try { await api('/api/media', json('POST', suggestion)); await onRefresh(); setNotice(`${suggestion.title} wurde hinzugefügt.`) }
    catch (e) { setError(e instanceof Error ? e.message : 'Hinzufügen fehlgeschlagen') }
  }
  const edit = (item: Media) => {
    setSelected(item); setWatch(item.watch_state || 'unwatched')
    setSeason(String(item.season_number ?? 1)); setEpisode(String(item.episode_number ?? 1))
    setStatus(item.status); setError(''); setNotice('')
  }
  const save = async () => {
    if (!selected) return
    try {
      const value = Number(season), ep = Number(episode)
      if ((watch === 'through_episode' || watch === 'season_completed') && (!Number.isInteger(value) || value < 1)) throw new Error('Bitte eine gültige Staffelnummer eingeben.')
      if (watch === 'through_episode' && (!Number.isInteger(ep) || ep < 1)) throw new Error('Bitte eine gültige Folgennummer eingeben.')
      await api(`/api/media/${selected.id}/watch`, json('PATCH', { watch_state: watch, season_number: watch === 'through_episode' || watch === 'season_completed' ? value : null, episode_number: watch === 'through_episode' ? ep : null }))
      await api(`/api/media/${selected.id}/status`, json('PATCH', { status }))
      await onRefresh(); setSelected(null); setNotice('Fortschritt gespeichert.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Speichern fehlgeschlagen') }
  }
  const remove = async () => {
    if (!selected || !window.confirm(`„${selected.title}“ wirklich aus der Sammlung entfernen?`)) return
    try { await api(`/api/media/${selected.id}`, { method: 'DELETE' }); await onRefresh(); setSelected(null); setNotice('Titel entfernt.') }
    catch (e) { setError(e instanceof Error ? e.message : 'Entfernen fehlgeschlagen') }
  }
  const filtered = items.filter(item => (page !== 'Wunschliste' || item.status === 'wishlist') && (filter === 'all' || item.kind === filter))
  const progress = (item: Media) => item.watch_state === 'through_episode' ? `S${item.season_number} · bis Folge ${item.episode_number}` : item.watch_state === 'season_completed' ? `Staffel ${item.season_number} gesehen` : watchLabels[item.watch_state] || 'Nicht gesehen'
  return <div className="library-view">
    {notice && <div className="library-notice">{notice}</div>}
    {error && <div className="warning" role="alert">{error}</div>}
    {page === 'Entdecken' ? <><ImageAnalyzer onRefresh={onRefresh}/><section className="panel library-panel">
      <div className="panel-heading"><div><h3>Medien suchen und hinzufügen</h3><p>Suche nach Filmen, Serien und Anime – oder erfasse einen Titel direkt.</p></div><Search size={22}/></div>
      <div className="library-search">
        <label>Medientyp <select value={kind} onChange={e => { setKind(e.target.value as typeof kind); setSuggestions([]) }}>{categories.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}</select></label>
        <label className="wide">Titel suchen <div className="search-large"><Search size={18}/><input value={term} onChange={e => setTerm(e.target.value)} placeholder="z. B. One Piece, Interstellar ..." maxLength={120}/>{busy && <Loader2 className="spin" size={17}/>}</div></label>
      </div>
      <div className="results">
        {suggestions.map(s => <article className="result-card" key={s.provider + '-' + s.provider_id}>
          {s.poster_url ? <img src={s.poster_url} alt="" loading="lazy"/> : <div className="poster-placeholder"><Film/></div>}
          <div className="result-details"><strong>{s.title}</strong><small>{s.release_year ?? 'Jahr unbekannt'} · {categories.find(c => c.value === s.kind)?.label} · {s.provider === 'anilist' ? 'AniList' : 'TMDB'}</small></div>
          <button className="primary-btn" onClick={() => void add(s)}><Plus size={16}/> Hinzufügen</button>
        </article>)}
        {term.trim().length > 1 && !busy && suggestions.length === 0 && !error && <p className="library-muted">Keine Treffer gefunden. Du kannst den Titel manuell hinzufügen.</p>}
      </div>
      <div className="manual-add"><div><strong>Manuell hinzufügen</strong><p>Funktioniert auch ohne TMDB-API-Schlüssel und bei unbekannten Titeln.</p></div><button className="outline-btn" disabled={!term.trim()} onClick={() => void add({ title: term.trim(), kind })}><Plus size={16}/> „{term.trim() || 'Titel'}“ hinzufügen</button></div>
      <p className="library-muted">Anime werden über AniList gesucht. Film- und Seriensuche benötigt einen kostenlosen TMDB-API-Schlüssel in der Serverkonfiguration.</p>
    </section></> : <section className="panel library-panel">
      <div className="panel-heading"><div><h3>{page === 'Wunschliste' ? 'Deine Wunschliste' : 'Deine Mediensammlung'}</h3><p>Sehfortschritt und Mediathekstatus unabhängig voneinander verwalten.</p></div><span className="panel-count">{filtered.length} Titel</span></div>
      <div className="library-tabs">{[{ value: 'all', label: 'Alle' }, ...categories].map(c => <button key={c.value} className={filter === c.value ? 'active' : ''} onClick={() => setFilter(c.value)}>{c.label}</button>)}</div>
      {filtered.length ? <div className="library-grid">{filtered.map(item => <button className="library-tile" key={item.id} onClick={() => edit(item)}>
        {item.poster_url ? <img src={item.poster_url} alt="" loading="lazy" /> : <span className="tile-fallback">{item.kind === 'movie' ? <Film/> : <Tv/>}</span>}
        <span className="tile-content"><strong>{item.title}</strong><small>{item.release_year || categories.find(c => c.value === item.kind)?.label} · {statusLabels[item.status] || item.status}</small><span className="watch-tag">{progress(item)}</span></span>
      </button>)}</div> : <div className="library-empty"><Heart size={30}/><h3>Noch keine Titel vorhanden.</h3><p>Wechsle zu „Entdecken“, um deine ersten Filme, Serien oder Anime hinzuzufügen.</p></div>}
    </section>}
    {selected && <div className="dialog-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) setSelected(null) }}><section className="edit-dialog" role="dialog" aria-modal="true" aria-label="Sehfortschritt bearbeiten">
      <div className="dialog-head"><div><small>MEDIUM BEARBEITEN</small><h2>{selected.title}</h2></div><button aria-label="Schließen" onClick={() => setSelected(null)}><X size={20}/></button></div>
      <label>In meiner Mediathek <select value={status} onChange={e => setStatus(e.target.value)}>{Object.entries(statusLabels).map(([value,label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <label>Sehfortschritt <select value={watch} onChange={e => setWatch(e.target.value)}>
        <option value="unwatched">Nicht gesehen</option><option value="completed">{selected.kind === 'movie' ? 'Gesehen' : 'Komplett gesehen'}</option>
        {selected.kind !== 'movie' && <><option value="through_episode">Bis zu einer Folge gesehen</option><option value="season_completed">Staffel vollständig gesehen</option></>}
      </select></label>
      {(watch === 'through_episode' || watch === 'season_completed') && <div className="dialog-fields">
        <label>Staffel <input type="number" min="1" max="999" value={season} onChange={e => setSeason(e.target.value)}/></label>
        {watch === 'through_episode' && <label>Folge <input type="number" min="1" max="99999" value={episode} onChange={e => setEpisode(e.target.value)}/></label>}
      </div>}
      {error && <p className="dialog-error">{error}</p>}
      <div className="dialog-actions"><button className="delete-btn" onClick={() => void remove()}><Trash2 size={16}/> Entfernen</button><button className="primary-btn" onClick={() => void save()}><Check size={17}/> Speichern</button></div>
    </section></div>}
  </div>
}
