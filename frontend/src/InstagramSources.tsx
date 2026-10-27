import { useEffect, useState } from 'react'
import { ExternalLink, Instagram, Link2, Trash2 } from 'lucide-react'

export type InstagramSource = {
  id:number; url:string; shortcode:string; kind:string;
  created_at:string|null; media_ids:number[]; import_mode:string; existing?:boolean
}
type Props = { selectedId:number|null; onSelect:(id:number|null)=>void }

export default function InstagramSources({selectedId,onSelect}:Props){
 const [url,setUrl]=useState('')
 const [sources,setSources]=useState<InstagramSource[]>([])
 const [error,setError]=useState('')
 const [notice,setNotice]=useState('')
 const [busy,setBusy]=useState(false)
 const refresh=async()=>{
  const response=await fetch('/api/instagram/sources')
  if(!response.ok)throw new Error('Quellen konnten nicht geladen werden')
  setSources(await response.json())
 }
 useEffect(()=>{void refresh().catch(e=>setError(String(e)))},[])
 const save=async()=>{
  setBusy(true);setError('');setNotice('')
  try{
   const response=await fetch('/api/instagram/sources',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url.trim()})})
   const data=await response.json()
   if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Link konnte nicht gespeichert werden')
   await refresh()
   onSelect(data.id);setUrl('')
   setNotice(data.existing?'Beitrag war bereits gespeichert. Du kannst weitere Bilder zuordnen.':'Beitrag gespeichert. Lade jetzt die zugehörigen Screenshots hoch.')
  }catch(e){setError(e instanceof Error?e.message:'Unbekannter Fehler')}
  finally{setBusy(false)}
 }
 const remove=async(id:number)=>{
  if(!window.confirm('Instagram-Quelle und Verknüpfungen entfernen? Die Filme bleiben erhalten.'))return
  const response=await fetch(`/api/instagram/sources/${id}`,{method:'DELETE'})
  if(!response.ok){setError('Quelle konnte nicht gelöscht werden');return}
  if(selectedId===id)onSelect(null)
  await refresh()
 }
 return <section className="panel instagram-panel">
  <div className="panel-heading"><div><h3><Instagram size={18} style={{verticalAlign:'middle',marginRight:8,color:'#d88bf1'}}/> Instagram-Import</h3><p>Beitrag merken und Screenshots für die Bilderkennung zuordnen.</p></div><span className="panel-count">LINK + BILDER</span></div>
  <div className="ig-input">
   <label htmlFor="ig-link">Instagram-Beitragslink (Post, Carousel oder Reel)</label>
   <div><input id="ig-link" type="url" placeholder="https://www.instagram.com/p/..." value={url} onChange={e=>setUrl(e.target.value)} maxLength={2048}/><button className="primary-btn" disabled={busy||!url.trim()} onClick={()=>void save()}><Link2 size={16}/> Link merken</button></div>
  </div>
  <p className="library-muted">Der Link allein liefert keine Medienbilder. Öffne den Beitrag bei Instagram und lade darunter deine eigenen Screenshots bzw. gespeicherten Bilder hoch. Mehrere Bilder eines Carousels können gemeinsam analysiert werden. Es werden keine Instagram-Logins oder Scraping-Tricks verwendet.</p>
  {error&&<div className="warning" role="alert">{error}</div>}{notice&&<div className="library-notice" role="status">{notice}</div>}
  <div className="ig-sources">
   {sources.length===0?<p>Du hast noch keine Instagram-Beiträge erfasst.</p>:sources.map(src=><div key={src.id} className={`ig-source ${selectedId===src.id?'active':''}`}>
    <label><input type="radio" checked={selectedId===src.id} onChange={()=>onSelect(src.id)} name="igsource"/><span><strong>{src.kind==='reel'?'Reel':src.kind==='video'?'Video':'Beitrag'} · {src.shortcode}</strong><small>{src.media_ids.length} verknüpfte Titel</small></span></label>
    <a href={src.url} target="_blank" rel="noopener noreferrer" title="Bei Instagram öffnen"><ExternalLink size={17}/></a>
    <button title="Quelle löschen" onClick={()=>void remove(src.id)}><Trash2 size={16}/></button>
   </div>)}
  </div>
  {selectedId!==null&&<button className="ig-clear" onClick={()=>onSelect(null)}>Quelle abwählen – Bilder ohne Instagram-Beitrag analysieren</button>}
 </section>
}
