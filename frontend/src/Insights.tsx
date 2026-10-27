import { useEffect, useState } from 'react'
import { Activity, BarChart3, Clapperboard, Database, Film, Heart, Instagram, RefreshCw, Sparkles, Tv } from 'lucide-react'

type CountMap = Record<string,number>
type Insight = {
 generated_at:string
 collection:{total:number;kinds:CountMap;statuses:CountMap;watch_states:CountMap;tracked_episodes:number;titles_with_episode_tracking:number;monthly_added:{month:string;count:number}[]}
 jellyfin:{synced:boolean;last_sync:string|null;counts:{movies:number;series:number;episodes:number};match_status:CountMap;matches:{media_id:number;title:string;status:string;episodes_found:number}[]}
 instagram:{sources:number;kinds:CountMap;unique_titles:number;total_mentions:number;most_mentioned:{id:number;title:string;kind:string;poster_url:string|null;mentions:number;watched_episodes:number}[];top_sources:{id:number;url:string;kind:string;titles:number}[]}
 notes:string[]
}
const kindNames:CountMap = {}
const colors:Record<string,string>={movie:'#60b8f5',series:'#ac8afa',anime:'#50d1c7',wishlist:'#90b2ec',planned:'#8c8df5',processing:'#f6c071',owned:'#58cba9',ignored:'#8794af',unwatched:'#8395b7',completed:'#51cfa8',through_episode:'#f7c16b',season_completed:'#aa93ec',present:'#62d4a5',series_only:'#e9bc72',missing:'#ee91a1',ambiguous:'#b7a0ff'}
function BarSet({values,names}: {values:CountMap;names:Record<string,string>}) {
 const total=Object.values(values).reduce((a,b)=>a+b,0)
 return <div className="insight-bars">{Object.entries(names).map(([key,label])=>{
  const count=values[key]||0
  return <div className="insight-bar-row" key={key}><span>{label}</span><div className="insight-bar-track"><span style={{width:total?`${count/total*100}%`:'0%',background:colors[key]||'#82b8f0'}}/></div><strong>{count}</strong></div>
 })}</div>
}
export default function Insights(){
 const [data,setData]=useState<Insight|null>(null)
 const [loading,setLoading]=useState(true)
 const [error,setError]=useState('')
 const refresh=async()=>{
  setLoading(true);setError('')
  try{
   const response=await fetch('/api/insights')
   if(!response.ok)throw new Error('Insights konnten nicht geladen werden')
   setData(await response.json())
  }catch(e){setError(e instanceof Error?e.message:'Unbekannter Fehler')}
  finally{setLoading(false)}
 }
 useEffect(()=>{void refresh()},[])
 return <div className="insights-page">
  <div className="insights-top"><div><h2><BarChart3 size={21}/> Deine Medien in Zahlen</h2><p>Auswertungen aus deiner Cinearis-Datenbank, Instagram-Quellen und dem letzten Jellyfin-Abgleich.</p></div><button className="outline-btn" disabled={loading} onClick={()=>void refresh()}><RefreshCw size={16}/> Aktualisieren</button></div>
  {error&&<div className="warning" role="alert">{error}</div>}
  {loading&&!data&&<p className="library-muted">Statistiken werden geladen …</p>}
  {data&&<>
   <div className="insight-metrics">
    {[{name:'Titel insgesamt',value:data.collection.total,icon:Clapperboard},{name:'Komplett gesehen',value:data.collection.watch_states.completed||0,icon:Film},{name:'Markierte Episoden',value:data.collection.tracked_episodes,icon:Tv},{name:'Instagram-Fundstellen',value:data.instagram.total_mentions,icon:Instagram}].map(({name,value,icon:Icon})=><div className="insight-metric" key={name}><span>{name}</span><Icon size={21}/><strong>{value.toLocaleString('de-DE')}</strong></div>)}
   </div>
   <div className="insight-panels">
    <section className="panel insight-panel"><h3><Clapperboard size={18}/> Medienarten</h3><BarSet values={data.collection.kinds} names={{movie:'Filme',series:'Serien',anime:'Anime'}}/></section>
    <section className="panel insight-panel"><h3><Heart size={18}/> Sammlungsstatus</h3><BarSet values={data.collection.statuses} names={{wishlist:'Wunschliste',planned:'Geplant',processing:'In Bearbeitung',owned:'Vorhanden',ignored:'Ignoriert'}}/></section>
    <section className="panel insight-panel"><h3><Activity size={18}/> Sehfortschritt</h3><BarSet values={data.collection.watch_states} names={{unwatched:'Ungesehen',completed:'Komplett gesehen',through_episode:'Bis Folge gesehen',season_completed:'Staffel gesehen'}}/><p className="insight-note">{data.collection.titles_with_episode_tracking} Serien/Animes besitzen detaillierte Episodeneinträge.</p></section>
    <section className="panel insight-panel"><h3><Database size={18}/> Jellyfin-Abgleich</h3>{data.jellyfin.synced?<><BarSet values={data.jellyfin.match_status} names={{present:'Gefunden',series_only:'Serie ohne Episoden',missing:'Nicht gefunden',ambiguous:'Unklar'}}/><p className="insight-note">Letzter erfolgreicher Scan: {data.jellyfin.last_sync?new Date(data.jellyfin.last_sync).toLocaleString('de-DE'):'unbekannt'}</p></>:<p className="insight-note">Noch kein Jellyfin-Snapshot vorhanden. Starte den Abgleich in „Meine Sammlung“.</p>}</section>
   </div>
   <div className="insight-panels">
    <section className="panel insight-panel"><h3><Sparkles size={18}/> Häufigste Empfehlungen</h3>{data.instagram.most_mentioned.length?<div className="insight-ranking">{data.instagram.most_mentioned.map((item,index)=><div key={item.id} className="insight-rank"><span className="insight-rank-number">{index+1}</span>{item.poster_url?<img src={item.poster_url} loading="lazy" alt=""/>:<div className="insight-poster"><Film size={18}/></div>}<div><strong>{item.title}</strong><small>{item.kind}</small></div><span>{item.mentions} {item.mentions===1?'Quelle':'Quellen'}</span></div>)}</div>:<p className="insight-note">Noch keine Titel mit Instagram-Quellen verknüpft.</p>}</section>
    <section className="panel insight-panel"><h3><Instagram size={18}/> Quellenübersicht</h3><div className="insight-source-summary"><span>{data.instagram.sources} gespeicherte Beiträge</span><span>{data.instagram.unique_titles} unterschiedliche Titel entdeckt</span></div>{data.instagram.top_sources.length?<div className="insight-ranking">{data.instagram.top_sources.map(src=><div key={src.id} className="insight-rank"><Instagram size={17}/><a target="_blank" rel="noopener noreferrer" href={src.url}>{src.kind} · {src.url.split('/').filter(Boolean).pop()}</a><span>{src.titles} Titel</span></div>)}</div>:<p className="insight-note">Noch keine verknüpften Instagram-Quellen.</p>}</section>
   </div>
   <section className="panel insight-panel"><h3><BarChart3 size={18}/> Neue Titel pro Monat</h3>{data.collection.monthly_added.length?<div className="insight-timeline">{data.collection.monthly_added.slice(-18).map(row=><div key={row.month}><strong>{row.count}</strong><span style={{height:`${Math.max(5,row.count/Math.max(1,...data.collection.monthly_added.map(x=>x.count))*105)}px`}}/><small>{row.month}</small></div>)}</div>:<p className="insight-note">Sobald du Titel hinzugefügt hast, erscheint hier der Verlauf.</p>}</section>
   <p className="insight-disclaimer">{data.notes.join(' ')}</p>
  </>}
 </div>
}
