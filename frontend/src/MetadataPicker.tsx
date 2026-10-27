import { useEffect, useState } from 'react'
import { Check, Loader2, Search, X } from 'lucide-react'

export type MetaMatch = {
  title: string; original_title?: string | null; aliases?: string[]; description?: string | null
  kind: 'movie' | 'series' | 'anime'; provider: 'tmdb' | 'anilist'; provider_id: string
  poster_url?: string | null; release_year?: number | null; match_score?: number
}
type Props = {
  kind: 'movie' | 'series' | 'anime'; title: string
  onSelect: (match: MetaMatch) => void; onClose: () => void
}

export default function MetadataPicker({ kind, title, onSelect, onClose }: Props) {
  const [term,setTerm] = useState(title)
  const [items,setItems] = useState<MetaMatch[]>([])
  const [busy,setBusy] = useState(false)
  const [error,setError] = useState('')
  useEffect(() => { setTerm(title) },[title])
  useEffect(() => {
    if(term.trim().length<2){setItems([]);return}
    const controller=new AbortController()
    const timer=setTimeout(async()=>{
      setBusy(true);setError('')
      try{
        const response=await fetch(`/api/metadata/search?kind=${kind}&q=${encodeURIComponent(term.trim())}`,{signal:controller.signal})
        const body=await response.json()
        if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:'Metadatensuche fehlgeschlagen')
        if(!controller.signal.aborted)setItems(body)
      }catch(e){if(!controller.signal.aborted){setItems([]);setError(e instanceof Error?e.message:'Suche fehlgeschlagen')}}
      finally{if(!controller.signal.aborted)setBusy(false)}
    },400)
    return()=>{clearTimeout(timer);controller.abort()}
  },[kind,term])
  return <div className="metadata-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose()}}>
    <section className="metadata-dialog" role="dialog" aria-modal="true" aria-label="Titel mit Metadaten abgleichen">
      <div className="dialog-head"><div><small>TITEL ZUORDNEN</small><h2>Metadaten abgleichen</h2></div><button onClick={onClose} aria-label="Schließen"><X size={20}/></button></div>
      <p className="library-muted">Wähle den tatsächlich passenden Eintrag. Ähnliche Titel sind nicht automatisch identisch.</p>
      <label className="metadata-search"><Search size={18}/><input aria-label="Nach Titel suchen" value={term} onChange={e=>setTerm(e.target.value)} autoFocus/>{busy&&<Loader2 className="spin" size={16}/>}</label>
      {error&&<div className="warning" role="alert">{error}</div>}
      <div className="metadata-results">
        {!busy&&!items.length&&!error&&<p className="library-muted">Keine Treffer. Passe den Suchbegriff an oder speichere ohne Metadaten.</p>}
        {items.map(item=><button className="metadata-hit" key={item.provider+item.provider_id} onClick={()=>onSelect(item)}>
          {item.poster_url?<img src={item.poster_url} alt="" loading="lazy"/>:<span className="metadata-no-poster">🎬</span>}
          <span><strong>{item.title}</strong><small>{item.original_title&&item.original_title!==item.title?item.original_title+' · ':''}{item.release_year??'Jahr unbekannt'}</small><small>{item.provider==='tmdb'?'TMDB':'AniList'} · ID {item.provider_id} · Ähnlichkeit {Math.round((item.match_score??0)*100)} %</small></span><Check size={18}/>
        </button>)}
      </div>
      <button className="outline-btn" onClick={onClose}>Ohne Zuordnung fortfahren</button>
    </section>
  </div>
}
