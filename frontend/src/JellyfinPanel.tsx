import { useEffect, useState } from 'react'
import { Check, Database, Loader2, RefreshCw, ShieldCheck, AlertTriangle } from 'lucide-react'

type Status={configured:boolean;last_sync:string|null;movie_count:number;series_count:number;episode_count:number;read_only:boolean}
export type Match={media_id:number;status:'present'|'series_only'|'missing'|'ambiguous';match_method?:string;matched_title?:string;jellyfin_id?:string;episodes_found?:number;seasons?:Record<string,number[]>;reason?:string}
type Matches={synced:boolean;matches:Match[]}
type Props={onMatches:(items:Record<number,Match>,synced:boolean)=>void}
const initial:Status={configured:false,last_sync:null,movie_count:0,series_count:0,episode_count:0,read_only:true}

export default function JellyfinPanel({onMatches}:Props){
 const [state,setState]=useState<Status>(initial)
 const [matches,setMatches]=useState<Match[]>([])
 const [loading,setLoading]=useState(false)
 const [error,setError]=useState('')
 const [notice,setNotice]=useState('')
 const [synced,setSynced]=useState(false)
 const refresh=async()=>{
  const [a,b]=await Promise.all([fetch('/api/jellyfin/status'),fetch('/api/jellyfin/matches')])
  if(!a.ok||!b.ok)throw new Error('Jellyfin-Status nicht abrufbar')
  const s:Status=await a.json(),m:Matches=await b.json()
  setState(s);setMatches(m.matches);setSynced(m.synced)
  onMatches(Object.fromEntries(m.matches.map(item=>[item.media_id,item])),m.synced)
 }
 useEffect(()=>{void refresh().catch(e=>setError(String(e)))},[])
 const synchronize=async()=>{
  setLoading(true);setError('');setNotice('')
  try{
   const r=await fetch('/api/jellyfin/sync',{method:'POST'})
   const data=await r.json()
   if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:'Synchronisierung fehlgeschlagen')
   await refresh()
   setNotice(`Jellyfin synchronisiert: ${data.movies} Filme, ${data.series} Serien, ${data.episodes} Episoden. ${data.matched} Titel zugeordnet.`)
  }catch(e){setError(e instanceof Error?e.message:'Jellyfin-Fehler')}
  finally{setLoading(false)}
 }
 const found=matches.filter(m=>m.status==='present'||m.status==='series_only').length
 const missing=matches.filter(m=>m.status==='missing').length
 const ambiguous=matches.filter(m=>m.status==='ambiguous').length
 return <section className="panel jelly-panel">
   <div className="panel-heading"><div><h3><Database size={18} style={{verticalAlign:'middle',marginRight:8,color:'#66ccff'}}/> Jellyfin-Bibliothek</h3><p>Medienbestand aus Velaris / Jellyfin vergleichen – unabhängig vom Sehfortschritt.</p></div><span className="panel-count"><ShieldCheck size={14}/> NUR LESEN</span></div>
   <div className="jelly-summary">
    <div><small>Filme auf Jellyfin</small><strong>{state.movie_count}</strong></div>
    <div><small>Serien auf Jellyfin</small><strong>{state.series_count}</strong></div>
    <div><small>Episoden auf Jellyfin</small><strong>{state.episode_count}</strong></div>
    <div><small>Zuletzt synchronisiert</small><strong className="jelly-date">{state.last_sync?new Date(state.last_sync).toLocaleString('de-DE'):'Noch nie'}</strong></div>
   </div>
   <div className="jelly-actions">
    <span className={state.configured?'jelly-connected':'jelly-unconfigured'}>{state.configured?'Konfiguration vorhanden':'JELLYFIN_URL / JELLYFIN_API_KEY fehlen'}</span>
    <button className="primary-btn" disabled={!state.configured||loading} onClick={()=>void synchronize()}>{loading?<Loader2 size={16} className="spin"/>:<RefreshCw size={16}/>} {loading?'Bibliothek wird gelesen …':'Jetzt mit Jellyfin vergleichen'}</button>
   </div>
   {error&&<div className="warning" role="alert"><AlertTriangle size={16}/> {error}</div>}
   {notice&&<div className="library-notice" role="status">{notice}</div>}
   {synced&&<div className="jelly-match-stats"><span><Check size={15}/> {found} gefunden</span><span>{missing} nicht gefunden</span><span>{ambiguous} unklar</span></div>}
   <p className="library-muted">Der Abgleich verwendet zuerst passende TMDB-IDs, dann eindeutige Titel- und Jahresübereinstimmungen. Bei Serien werden ausschließlich Episoden der konkret zugeordneten Jellyfin-Serie gezählt. „Nicht gefunden“ bedeutet nur: kein eindeutiger Treffer im letzten Scan.</p>
 </section>
}
