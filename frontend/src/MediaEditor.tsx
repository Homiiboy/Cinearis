import { useEffect, useState } from 'react'
import { Check, ChevronDown, Edit3, Search, Trash2, Tv, X } from 'lucide-react'
import type { Media } from './Library'

type Episode = { season:number; episode:number }
type Props={ item:Media; onClose:()=>void; onRefresh:()=>Promise<void> }
const labels:Record<string,string>={wishlist:'Wunschliste',planned:'Geplant',processing:'In Bearbeitung',owned:'Vorhanden',ignored:'Ignoriert'}

async function call(path:string,method='GET',payload?:object) {
 const res=await fetch(path,{method,headers:payload?{'Content-Type':'application/json'}:undefined,body:payload?JSON.stringify(payload):undefined})
 if(!res.ok){let detail='Anfrage fehlgeschlagen';try{const data=await res.json();if(typeof data.detail==='string')detail=data.detail}catch{}throw new Error(detail)}
 return res.json()
}

export default function MediaEditor({item,onClose,onRefresh}:Props){
 const [title,setTitle]=useState(item.title)
 const [year,setYear]=useState(item.release_year?.toString()||'')
 const [description,setDescription]=useState(item.description||'')
 const [status,setStatus]=useState(item.status)
 const [movieWatched,setMovieWatched]=useState(item.watch_state==='completed')
 const [watched,setWatched]=useState<Episode[]>([])
 const [season,setSeason]=useState('1')
 const [episode,setEpisode]=useState('1')
 const [seasonCount,setSeasonCount]=useState('12')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const [notice,setNotice]=useState('')
 useEffect(()=>{
  if(item.kind==='movie')return
  let active=true
  call(`/api/media/${item.id}/episodes`).then(data=>{if(active)setWatched(data)}).catch(e=>{if(active)setError(String(e))})
  return()=>{active=false}
 },[item.id,item.kind])
 const execute=async(action:()=>Promise<unknown>,message:string)=>{
  setBusy(true);setError('');setNotice('')
  try{await action();await onRefresh();setNotice(message)}
  catch(e){setError(e instanceof Error?e.message:'Fehler')}
  finally{setBusy(false)}
 }
 const saveBasics=()=>execute(async()=>{
  const number=year.trim()?Number(year):null
  if(number!==null&&(!Number.isInteger(number)||number<1870||number>2200))throw new Error('Ungültiges Erscheinungsjahr')
  await call(`/api/media/${item.id}`,'PATCH',{title,release_year:number,description})
  await call(`/api/media/${item.id}/status`,'PATCH',{status})
  if(item.kind==='movie')await call(`/api/media/${item.id}/watch`,'PATCH',{watch_state:movieWatched?'completed':'unwatched'})
 },'Änderungen gespeichert')
 const n=(value:string,min=1,max=99999)=>{const x=Number(value);if(!Number.isInteger(x)||x<min||x>max)throw new Error('Bitte gültige Nummern eingeben.');return x}
 const setOne=(value:boolean)=>execute(async()=>{
  const s=n(season,0,999),e=n(episode)
  await call(`/api/media/${item.id}/episodes`,'PUT',{season:s,episode:e,watched:value})
  setWatched(previous=>value?[...previous.filter(p=>!(p.season===s&&p.episode===e)),{season:s,episode:e}]:previous.filter(p=>!(p.season===s&&p.episode===e)))
 },value?'Episode als gesehen markiert':'Episode als ungesehen markiert')
 const setWhole=(value:boolean)=>execute(async()=>{
  const s=n(season,0,999), count=n(seasonCount,1,2000)
  await call(`/api/media/${item.id}/seasons`,'PUT',{season:s,episode_count:count,watched:value})
  const all=Array.from({length:count},(_,i)=>({season:s,episode:i+1}))
  setWatched(previous=>value?[...previous.filter(p=>!(p.season===s&&p.episode<=count)),...all]:previous.filter(p=>!(p.season===s&&p.episode<=count)))
 },value?'Staffelbereich als gesehen markiert':'Staffelbereich als ungesehen markiert')
 const grouped=[...new Set(watched.map(x=>x.season))].sort((a,b)=>a-b)
 return <div className="collection-editor-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose()}}>
 <section role="dialog" aria-modal="true" aria-label="Medium bearbeiten" className="collection-editor">
  <div className="dialog-head"><div><small>SAMMLUNG BEARBEITEN · v0.4.0</small><h2>{item.title}</h2></div><button onClick={onClose} aria-label="Schließen"><X size={20}/></button></div>
  <div className="editor-fields">
   <label>Titel<input maxLength={300} value={title} onChange={e=>setTitle(e.target.value)}/></label>
   <label>Jahr<input type="number" min={1870} max={2200} value={year} onChange={e=>setYear(e.target.value)}/></label>
   <label>Status<select value={status} onChange={e=>setStatus(e.target.value)}>{Object.entries(labels).map(([v,label])=><option key={v} value={v}>{label}</option>)}</select></label>
   <label className="wide">Beschreibung<textarea rows={3} maxLength={1500} value={description} onChange={e=>setDescription(e.target.value)}/></label>
  </div>
  {item.kind==='movie'?<label className="editor-check"><input type="checkbox" checked={movieWatched} onChange={e=>setMovieWatched(e.target.checked)}/> Film gesehen</label>:<>
   <div className="editor-separator"><Tv size={17}/> Episoden & Staffeln</div>
   <p className="library-muted">Du kannst beliebige Staffeln einzeln dokumentieren – auch Specials als Staffel 0. Die Anzahl der Episoden gibst du selbst vor.</p>
   <div className="editor-fields">
    <label>Staffel<input type="number" min={0} max={999} value={season} onChange={e=>setSeason(e.target.value)}/></label>
    <label>Folge<input type="number" min={1} max={99999} value={episode} onChange={e=>setEpisode(e.target.value)}/></label>
    <label>Episoden dieser Staffel<input type="number" min={1} max={2000} value={seasonCount} onChange={e=>setSeasonCount(e.target.value)}/></label>
   </div>
   <div className="editor-actions"><button disabled={busy} onClick={()=>void setOne(true)}><Check size={15}/> Folge gesehen</button><button disabled={busy} onClick={()=>void setOne(false)}>Folge zurücksetzen</button></div>
   <div className="editor-actions"><button disabled={busy} onClick={()=>void setWhole(true)}><Check size={15}/> Staffel gesehen</button><button disabled={busy} onClick={()=>void setWhole(false)}>Staffel zurücksetzen</button></div>
   <div className="episode-summary"><strong>Gesehene Episoden: {watched.length}</strong>{grouped.map(s=><details key={s}><summary>Staffel {s} · {watched.filter(e=>e.season===s).length} Episoden <ChevronDown size={14}/></summary><div>{watched.filter(e=>e.season===s).sort((a,b)=>a.episode-b.episode).map(e=><span key={e.episode}>E{e.episode}</span>)}</div></details>)}</div>
  </>}
  {error&&<div className="warning" role="alert">{error}</div>}{notice&&<div className="library-notice" role="status">{notice}</div>}
  <div className="editor-footer"><button className="outline-btn" onClick={onClose}>Schließen</button><button disabled={busy} className="primary-btn" onClick={()=>void saveBasics()}><Check size={16}/> Änderungen speichern</button></div>
 </section></div>
}
