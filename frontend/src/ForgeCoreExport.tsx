import { useEffect, useState } from 'react'
import { Download, FileJson, FileSpreadsheet, ShieldCheck } from 'lucide-react'

type Item = { cinearis_id:number;title:string;media_type:string;release_year:number|null;library_check:string }
type Preview = { items:Item[];count:number;jellyfin_snapshot:boolean;disclaimer:string }
export default function ForgeCoreExport(){
 const [data,setData]=useState<Preview|null>(null)
 const [error,setError]=useState('')
 const [busy,setBusy]=useState(false)
 const refresh=async()=>{
  setBusy(true);setError('')
  try {
   const response=await fetch('/api/forgecore/preview')
   if(!response.ok)throw new Error('Export-Vorschau konnte nicht geladen werden')
   setData(await response.json())
  }catch(e){setError(e instanceof Error?e.message:'Fehler')}
  finally{setBusy(false)}
 }
 useEffect(()=>{void refresh()},[])
 const download=(type:'json'|'csv')=>{
  // Downloads are same-origin and protected by nginx authentication.
  window.location.href=`/api/forgecore/export?format=${type}`
 }
 return <section className="panel forge-panel">
  <div className="panel-heading"><div><h3><Download size={18} style={{verticalAlign:'middle',marginRight:8,color:'#82cbfc'}}/> Übergabe an ForgeCore</h3><p>Eine geprüfte Liste fehlender Titel als JSON oder CSV exportieren.</p></div><span className="panel-count"><ShieldCheck size={13}/> KEINE DOWNLOADS</span></div>
  {error&&<div className="warning" role="alert">{error}</div>}
  <div className="forge-summary"><strong>{data?data.count:'–'}</strong><div><b>Titel für den Export</b><small>{data?.jellyfin_snapshot?'Abgleich anhand des letzten Jellyfin-Snapshots':'Ohne Jellyfin-Snapshot: nur persönliche Statuswerte'}</small></div></div>
  <div className="forge-buttons"><button disabled={busy} className="outline-btn" onClick={()=>void refresh()}>Vorschau aktualisieren</button><button className="outline-btn" onClick={()=>download('json')}><FileJson size={17}/> JSON exportieren</button><button className="primary-btn" onClick={()=>download('csv')}><FileSpreadsheet size={17}/> CSV exportieren</button></div>
  {data&&data.items.length>0&&<div className="forge-preview">{data.items.slice(0,10).map(item=><div key={item.cinearis_id}><span>{item.title}</span><small>{item.media_type} · {item.release_year||'ohne Jahr'}</small></div>)}{data.items.length>10&&<p>… und {data.items.length-10} weitere Titel</p>}</div>}
  <p className="library-muted">Dies ist ein sicherer Übergabe-Export, keine direkte ForgeCore-API-Integration. Es werden keine Downloads ausgelöst. Mehrdeutige Jellyfin-Treffer werden vorsichtshalber nicht als fehlend exportiert.</p>
 </section>
}
