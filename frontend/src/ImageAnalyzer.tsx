import { useEffect, useRef, useState } from 'react'
import { Check, ImagePlus, Loader2, Plus, ShieldAlert, Sparkles, Trash2 } from 'lucide-react'

type Kind = 'movie' | 'series' | 'anime'
type Candidate = { title: string; kind: Kind | 'unknown'; confidence: number; evidence: string; source: 'ocr' | 'vision'; selected: boolean }
type Result = { candidates: Omit<Candidate,'selected'>[]; ocr_text: string; vision_enabled: boolean; vision_error: string | null; files_processed: number; disclaimer: string }
type Props = { onRefresh: () => Promise<void> }
const kinds: { value: Kind; label: string }[] = [{ value:'movie',label:'Film' },{ value:'series',label:'Serie' },{ value:'anime',label:'Anime' }]

async function errorMessage(response: Response) {
  try { const json: unknown = await response.json(); if (json && typeof json === 'object' && 'detail' in json && typeof json.detail === 'string') return json.detail } catch { /* ignore */ }
  return 'Analyse fehlgeschlagen. Bitte erneut versuchen.'
}

export default function ImageAnalyzer({ onRefresh }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [files,setFiles] = useState<File[]>([])
  const [results,setResults] = useState<Candidate[]>([])
  const [ocrText,setOcrText] = useState('')
  const [vision,setVision] = useState(false)
  const [analyzing,setAnalyzing] = useState(false)
  const [saving,setSaving] = useState(false)
  const [error,setError] = useState('')
  const [info,setInfo] = useState('')
  const [visionError,setVisionError] = useState('')
  useEffect(() => { fetch('/api/analysis/config').then(r => r.ok ? r.json() : null).then(v => { if (v) setVision(Boolean(v.vision_enabled)) }).catch(() => {}) }, [])
  const addFiles = (list: FileList | null) => {
    if (!list) return
    const next = Array.from(list)
    setError(''); setResults([]); setOcrText('')
    if (next.length > 8 || next.some(f => f.size > 8*1024*1024 || !['image/png','image/jpeg','image/webp'].includes(f.type))) {
      setError('Bitte maximal 8 PNG-, JPEG- oder WEBP-Bilder mit jeweils höchstens 8 MB auswählen.')
      return
    }
    setFiles(next)
  }
  const analyze = async () => {
    if (!files.length) return
    setAnalyzing(true); setError(''); setInfo(''); setResults([])
    const body = new FormData()
    files.forEach(file => body.append('files',file))
    try {
      const res = await fetch('/api/analysis/images',{method:'POST',body})
      if (!res.ok) throw new Error(await errorMessage(res))
      const data:Result = await res.json()
      setResults(data.candidates.map(c => ({...c, selected:c.confidence>=0.7 && c.kind!=='unknown'})))
      setOcrText(data.ocr_text); setVisionError(data.vision_error ?? '')
      setInfo(`${data.files_processed} Bild(er) analysiert · ${data.candidates.length} Vorschläge. Bitte alle Ergebnisse überprüfen.`)
    } catch(e) { setError(e instanceof Error ? e.message : 'Analyse fehlgeschlagen') }
    finally { setAnalyzing(false) }
  }
  const change = (index:number,patch:Partial<Candidate>) => setResults(prev => prev.map((item,i) => i === index ? {...item,...patch}:item))
  const addCandidate = () => setResults(prev => [...prev,{title:'',kind:'unknown',confidence:0,evidence:'Manuell ergänzt',source:'ocr',selected:false}])
  const save = async () => {
    const chosen=results.filter(c => c.selected)
    if(!chosen.length){setError('Bitte mindestens einen geprüften Treffer auswählen.');return}
    if(chosen.some(c => !c.title.trim() || c.kind==='unknown')){setError('Bitte für alle ausgewählten Titel einen Namen und Medientyp festlegen.');return}
    setSaving(true);setError('')
    let saved=0,duplicates=0,failed=0
    for(const c of chosen){
      try {
        const response=await fetch('/api/media',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:c.title.trim(),kind:c.kind,status:'wishlist'})})
        if(response.status===409){duplicates++;continue}
        if(!response.ok){failed++;continue}
        saved++
      }catch{failed++}
    }
    await onRefresh()
    setResults(prev=>prev.map(c=> chosen.includes(c) && failed===0 ? {...c,selected:false}:c))
    setInfo(`${saved} hinzugefügt · ${duplicates} bereits vorhanden · ${failed} fehlgeschlagen`)
    if(failed) setError('Nicht alle Titel konnten gespeichert werden. Bitte überprüfe die Sammlung.')
    setSaving(false)
  }
  return <section className="panel analyzer-panel">
    <div className="panel-heading"><div><h3><Sparkles size={18} style={{verticalAlign:'middle',marginRight:8,color:'#78d4ff'}}/> Bilderkennung</h3><p>Poster, Screenshots oder Collagen hochladen und gefundene Titel prüfen.</p></div><span className="panel-count">{vision?'Vision + OCR':'Lokale OCR'}</span></div>
    <div className="upload-zone" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();addFiles(e.dataTransfer.files)}}>
      <input type="file" ref={input} accept="image/png,image/jpeg,image/webp" multiple hidden onChange={e=>addFiles(e.target.files)}/>
      <ImagePlus size={32}/>
      <strong>{files.length?files.map(f=>f.name).join(', '):'Bilder auswählen oder hier ablegen'}</strong>
      <p>Bis zu 8 Dateien · PNG, JPG, WEBP · maximal 8 MB pro Datei</p>
      <button className="outline-btn" onClick={()=>input.current?.click()}>Bilder auswählen</button>
    </div>
    <div className="analyze-controls">
      <p><ShieldAlert size={17}/> {vision?'Bilder werden zur Erkennung an den konfigurierten KI-Anbieter übermittelt.':'Nur lokale OCR aktiv. Für Bilderkennung von Szenen VISION_API_KEY konfigurieren.'}</p>
      <button className="primary-btn" disabled={!files.length || analyzing || saving} onClick={()=>void analyze()}>{analyzing?<Loader2 className="spin" size={17}/>:<Sparkles size={17}/>} {analyzing?'Analysiere …':'Bilder analysieren'}</button>
    </div>
    {error&&<div className="warning" role="alert">{error}</div>}
    {info&&<div className="library-notice" role="status">{info}</div>}
    {visionError&&<div className="warning" role="alert">{visionError} – OCR-Ergebnisse bleiben verfügbar.</div>}
    {results.length>0&&<div className="candidate-area">
      <div className="candidate-header"><h3>Erkannte Titel überprüfen</h3><span>Unklare Treffer bleiben zunächst abgewählt.</span></div>
      {results.map((item,index)=><div className="candidate-row" key={index}>
        <label className="candidate-check"><input type="checkbox" checked={item.selected} onChange={e=>change(index,{selected:e.target.checked})}/><span>Übernehmen</span></label>
        <input aria-label="Titel" value={item.title} placeholder="Titel eingeben" maxLength={300} onChange={e=>change(index,{title:e.target.value})}/>
        <select aria-label="Medientyp" value={item.kind} onChange={e=>change(index,{kind:e.target.value as Candidate['kind']})}>
          <option value="unknown">Unbekannt</option>{kinds.map(k=><option key={k.value} value={k.value}>{k.label}</option>)}
        </select>
        <span className={`confidence ${item.confidence>=0.8?'high':item.confidence>=0.55?'medium':'low'}`}>{Math.round(item.confidence*100)} % · {item.source==='ocr'?'OCR':'Vision'}</span>
        <button title="Vorschlag entfernen" className="icon-btn" onClick={()=>setResults(v=>v.filter((_,i)=>i!==index))}><Trash2 size={16}/></button>
        {item.evidence&&<small className="candidate-evidence">{item.evidence}</small>}
      </div>)}
      <div className="candidate-actions"><button className="outline-btn" onClick={addCandidate}><Plus size={16}/> Titel ergänzen</button><button className="primary-btn" disabled={saving} onClick={()=>void save()}>{saving?<Loader2 className="spin" size={16}/>:<Check size={16}/>} Geprüfte Titel hinzufügen</button></div>
    </div>}
    {ocrText&&<details className="ocr-details"><summary>Erkannten Bildtext anzeigen</summary><pre>{ocrText}</pre></details>}
  </section>
}
