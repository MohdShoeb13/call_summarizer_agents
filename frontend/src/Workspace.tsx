import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import * as Tabs from '@radix-ui/react-tabs'
import { AudioLines, ArrowUpRight, Check, ChevronRight, Download, FileAudio, FileText, History, LoaderCircle, Menu, Plus, Radio, ShieldCheck, Sparkles, Upload, X, AlertCircle } from 'lucide-react'
import { Brand } from './App'
import { Button } from './components/ui/button'
import { Waveform } from './components/Waveform'
import { request, active, type Call, type Sample, type Health } from './api'

const stages=['intake','transcription','summarization','quality','complete']
export default function Workspace(){
  const [params,setParams]=useSearchParams()
  const callId=params.get('call')
  const [call,setCall]=useState<Call|null>(null)
  const [history,setHistory]=useState<Call[]>([])
  const [samples,setSamples]=useState<Sample[]>([])
  const [health,setHealth]=useState<Health|null>(null)
  const [file,setFile]=useState<File|null>(null)
  const [sampleId,setSampleId]=useState(params.get('sample')||'billing-refund')
  const [mode,setMode]=useState<'upload'|'sample'>(params.has('sample')?'sample':'upload')
  const [replay,setReplay]=useState(true)
  const [simulate,setSimulate]=useState(false)
  const [submitting,setSubmitting]=useState(false)
  const [error,setError]=useState('')
  const [tab,setTab]=useState('summary')
  const [sidebar,setSidebar]=useState(false)
  const [mobile,setMobile]=useState(()=>window.matchMedia('(max-width: 700px)').matches)
  const [drag,setDrag]=useState(false)
  const [refresh,setRefresh]=useState(0)
  const [highlight,setHighlight]=useState<number|null>(null)
  const input=useRef<HTMLInputElement>(null)
  const sidebarRef=useRef<HTMLElement>(null)
  const audioUrls=useRef(new Map<string,string>())

  useEffect(()=>{
    const controller=new AbortController()
    Promise.all([request<Sample[]>('/api/samples',{signal:controller.signal}),request<Health>('/api/health',{signal:controller.signal}),request<Call[]>('/api/calls',{signal:controller.signal})]).then(([s,h,c])=>{setSamples(s);setHealth(h);setHistory(c)}).catch(e=>{if(e.name!=='AbortError')setError('Cannot connect to the server. Check that the backend is running, then retry.')})
    return ()=>controller.abort()
  },[refresh])
  useEffect(()=>()=>{audioUrls.current.forEach(URL.revokeObjectURL)},[])
  useEffect(()=>{
    const media=window.matchMedia('(max-width: 700px)')
    const change=()=>setMobile(media.matches)
    media.addEventListener('change',change)
    return ()=>media.removeEventListener('change',change)
  },[])
  useEffect(()=>{
    if(!mobile||!sidebar)return
    const previous=document.activeElement as HTMLElement|null
    const root=sidebarRef.current
    const controls=()=>Array.from(root?.querySelectorAll<HTMLElement>('a[href],button:not([disabled])')??[]).filter(el=>el.getClientRects().length)
    controls()[0]?.focus()
    const trap=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){setSidebar(false);return}
      if(event.key!=='Tab')return
      const items=controls();const first=items[0];const last=items[items.length-1]
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus()}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus()}
    }
    document.addEventListener('keydown',trap)
    return ()=>{document.removeEventListener('keydown',trap);previous?.focus()}
  },[mobile,sidebar])
  useEffect(()=>{
    if(!callId){setCall(null);return}
    let cancelled=false; let timer:ReturnType<typeof setTimeout>
    const controller=new AbortController()
    setCall(null)
    async function poll(){
      try{
        const result=await request<Call>(`/api/calls/${encodeURIComponent(callId!)}`,{signal:controller.signal})
        if(cancelled)return
        setCall(result)
        if(active(result))timer=setTimeout(poll,1000)
        else setHistory(await request<Call[]>('/api/calls',{signal:controller.signal}))
      }catch(e){if(!cancelled)setError(e instanceof Error?e.message:'Unable to load call.')}
    }
    void poll()
    return ()=>{cancelled=true;controller.abort();clearTimeout(timer)}
  },[callId,refresh])

  function chooseFile(next:File|undefined){
    if(!next)return
    if(!/\.(mp3|wav|m4a|txt|json)$/i.test(next.name)){setError('Choose an MP3, WAV, M4A, TXT, or JSON file.');return}
    if(!next.size||next.size>24*1024*1024){setError('Choose a nonempty file smaller than 24 MiB.');return}
    setFile(next);setError('')
  }
  async function submit(){
    setError('');setSubmitting(true)
    try{
      const body=new FormData()
      if(mode==='sample'){body.set('sample_id',sampleId);body.set('demo',String(replay));body.set('simulate_failure',String(replay&&simulate))}
      else if(file)body.set('file',file)
      else throw new Error('Choose a file first.')
      const result=await request<Call>('/api/calls',{method:'POST',body})
      if(mode==='upload'&&file&&/\.(mp3|wav|m4a)$/i.test(file.name))audioUrls.current.set(result.id,URL.createObjectURL(file))
      setCall(result);setHistory(old=>[result,...old]);setParams({call:result.id});setTab('summary')
    }catch(e){setError(e instanceof Error?e.message:'Unable to start analysis.')}
    finally{setSubmitting(false)}
  }
  function newCall(){setParams({});setCall(null);setError('');setFile(null);setSidebar(false)}
  function evidence(id:number){setTab('transcript');setHighlight(id);setTimeout(()=>{const el=document.getElementById(`segment-${id}`);el?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});el?.focus({preventScroll:true})},80)}
  const busy=active(call)
  const evidenceButtons=(ids:number[])=><div className="evidence-links">{ids.map(id=><button key={id} onClick={()=>evidence(id)} aria-label={`View transcript segment ${id}`}>#{String(id).padStart(2,'0')} <ArrowUpRight size={12}/></button>)}</div>

  return <div className="workspace"><a className="skip-link" href="#workspace-main">Skip to content</a>
    {sidebar&&<button className="sidebar-scrim" aria-label="Close history" onClick={()=>setSidebar(false)}/>}
    <aside ref={sidebarRef} inert={mobile&&!sidebar} className={`sidebar ${sidebar?'sidebar-open':''}`}><div className="sidebar-brand"><Brand/><button className="mobile-only icon-button" aria-label="Close history" onClick={()=>setSidebar(false)}><X size={20}/></button></div><Button onClick={newCall}><Plus size={17}/> New analysis</Button><div className="sidebar-label"><History size={14}/> CALL HISTORY <span>{history.length}</span></div><div className="history-list">{history.length===0?<p className="empty-history">Your conversations will live here.<br/>Start with a sample or your own call.</p>:history.map(item=><button key={item.id} className={`history-item ${callId===item.id?'selected':''}`} onClick={()=>{setParams({call:item.id});setSidebar(false);setError('')}}><FileText size={16}/><span>{item.title}<small>{item.demo?'Sample replay':'Your call'} · {item.status}</small></span><ChevronRight size={13}/></button>)}</div><div className="sidebar-bottom"><span className="icon-tile"><ShieldCheck size={18}/></span><div>Local workspace<small>History stored on this device</small></div></div></aside>
    <div className="workspace-body"><header className="workspace-header"><div><button className="mobile-only icon-button" aria-label="Open history" onClick={()=>setSidebar(true)}><Menu size={20}/></button><span>Workspace</span><ChevronRight size={14}/><strong>{call?'Call analysis':'New analysis'}</strong></div><span className="connection"><span className={`status-dot ${health?.ready?'':'status-muted'}`}/>{health?.ready?'OpenAI configured':'Sample replay available'}</span></header>
      <main id="workspace-main" className="workspace-main">
        {error&&<div className="error-banner" role="alert"><AlertCircle size={18}/><span>{error}</span><button onClick={()=>{setError('');setRefresh(x=>x+1)}}>Retry</button><button aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}
        {!callId?<>
          <div className="workspace-title"><span className="eyebrow">THE NEXT CONVERSATION STARTS HERE</span><h1>Find the signal.</h1><p>Bring a call. Leave with a clearer picture.</p></div>
          <div className="intake-grid"><section className="upload-panel"><div className="panel-heading"><span className="icon-tile"><AudioLines size={20}/></span><div><h2>A conversation worth understanding</h2><p>Audio or text. We’ll take it from here.</p></div></div>
            <div className="mode-switch" role="group" aria-label="Input source"><button aria-pressed={mode==='upload'} className={mode==='upload'?'selected':''} onClick={()=>setMode('upload')}><Upload size={15}/> Upload a call</button><button aria-pressed={mode==='sample'} className={mode==='sample'?'selected':''} onClick={()=>setMode('sample')}><Sparkles size={15}/> Explore a sample</button></div>
            {mode==='upload'?<><input ref={input} className="sr-only" type="file" tabIndex={-1} aria-label="Call file" accept=".mp3,.wav,.m4a,.txt,.json" onChange={e=>chooseFile(e.target.files?.[0])}/><button className={`dropzone ${drag?'dragging':''}`} onClick={()=>input.current?.click()} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);chooseFile(e.dataTransfer.files[0])}}><span className="upload-icon">{file?<FileAudio size={30}/>:<Upload size={30}/>}</span><strong>{file?file.name:'Drop your conversation here'}</strong><span>{file?`${(file.size/1024).toFixed(1)} KB · Click to replace`:'or browse files on your device'}</span><small>MP3, WAV, M4A, TXT, JSON · Up to 24 MiB</small></button><p className="privacy-note"><ShieldCheck size={14}/> Analysis sends call content to OpenAI. Audio isn’t saved to disk.</p></>:<div className="sample-form"><label htmlFor="sample">Choose a conversation</label><select id="sample" value={sampleId} onChange={e=>setSampleId(e.target.value)}>{samples.map(s=><option key={s.id} value={s.id}>{s.title} — {s.scenario}</option>)}</select><label className="checkbox-label"><input type="checkbox" checked={replay} onChange={e=>setReplay(e.target.checked)}/><span>Replay curated example<small>Prewritten results, no AI request or API key required.</small></span></label><label className="checkbox-label"><input type="checkbox" checked={simulate} disabled={!replay} onChange={e=>setSimulate(e.target.checked)}/><span>Demonstrate model fallback<small>Simulate a timeout and recovery in the activity log.</small></span></label>{!replay&&<p className="privacy-note">This will analyze the synthetic transcript using OpenAI.</p>}</div>}
            <Button className="analyze-button" disabled={submitting||(mode==='upload'&&!file)||(mode==='sample'&&!samples.length)} onClick={submit}>{submitting?<LoaderCircle size={17} className="spin"/>:<Sparkles size={17}/>} {mode==='sample'&&replay?'Replay sample':'Analyze conversation'} <ArrowUpRight size={17}/></Button>
          </section><aside className="expect-panel"><span className="eyebrow">ON THE OTHER SIDE</span><h2>Everything you need.<br/><span>Nothing lost in the noise.</span></h2><Waveform compact/>{[[FileText,'The essential story','Issue, outcome, and key moments.'],[ShieldCheck,'Quality with context','Four dimensions. Evidence for each score.'],[Check,'A clear way forward','Action items you can follow through on.']].map(([Icon,title,body])=>{const I=Icon as typeof FileText;return <div className="expect-item" key={String(title)}><I size={18}/><div><h3>{String(title)}</h3><p>{String(body)}</p></div></div>})}<div className="expect-foot">Five focused agents. One connected picture.</div></aside></div>
        </>:!call?<div className="loading-state" role="status"><LoaderCircle className="spin"/> Loading conversation…</div>:<>
          <div className="result-title"><div><span className="eyebrow">CONVERSATION INTELLIGENCE</span><h1>{call.title}</h1><p>{new Date(call.created_at).toLocaleString()} <span>·</span> {call.elapsed_seconds.toFixed(1)}s <span>·</span> <span className={`call-status ${call.status}`}>{call.status}</span></p></div><Button asChild variant="secondary"><a href={`/api/calls/${call.id}/export`} download><Download size={16}/> Export JSON</a></Button></div>
          {call.demo&&<div className="replay-banner"><Sparkles size={16}/> Sample replay · Curated example results, not live AI analysis.</div>}
          {call.error&&<div className="error-banner" role="alert"><AlertCircle size={18}/><span>{call.error}</span><Button variant="ghost" onClick={newCall}>New analysis</Button></div>}
          <div className="pipeline" aria-label="Analysis progress" aria-live="polite">{stages.map((stage,i)=><div key={stage} className={`${stages.indexOf(call.stage)>i||call.status==='completed'?'done':''} ${call.stage===stage?'current':''}`}><span>{stages.indexOf(call.stage)>i||call.status==='completed'?<Check size={13}/>:busy&&call.stage===stage?<LoaderCircle size={13} className="spin"/>:i+1}</span>{stage==='quality'?'Quality scoring':stage==='complete'?'Ready':stage}</div>)}</div>
          {audioUrls.current.has(call.id)&&<audio className="audio-player" controls src={audioUrls.current.get(call.id)} aria-label="Uploaded call recording"/>}
          <Tabs.Root value={tab} onValueChange={setTab} className="result-tabs"><Tabs.List aria-label="Call analysis sections"><Tabs.Trigger value="summary"><Sparkles size={16}/> Summary</Tabs.Trigger><Tabs.Trigger value="quality"><ShieldCheck size={16}/> Quality score</Tabs.Trigger><Tabs.Trigger value="transcript"><FileText size={16}/> Transcript <small>{call.transcript?.length||0}</small></Tabs.Trigger><Tabs.Trigger value="activity"><Radio size={16}/> Activity</Tabs.Trigger></Tabs.List>
            <Tabs.Content value="summary">{call.summary?<div className="summary-grid"><section className="result-panel"><div className="section-row"><span className="eyebrow">THE SHORT VERSION</span><span className="badge">{call.summary.resolution}</span></div><h2>{call.summary.issue}</h2><p className="summary-resolution">{call.summary.resolution_details}</p>{evidenceButtons(call.summary.evidence_ids)}<h3>Key moments</h3><ul className="key-points">{call.summary.key_points.map((p,i)=><li key={i}><span>{String(i+1).padStart(2,'0')}</span>{p}</li>)}</ul><div className="tags">{call.summary.tags.map(t=><span key={t}>{t}</span>)}</div></section><section className="result-panel action-panel"><span className="icon-tile"><Check size={20}/></span><h2>The next steps</h2>{call.summary.action_items.length?<ul>{call.summary.action_items.map((a,i)=><li key={i}><span className="action-number">{i+1}</span>{a}</li>)}</ul>:<p>No explicit follow-up actions identified.</p>}<small>Actions reflect what the conversation supports.</small></section></div>:<Empty busy={busy} text="A summary will appear here once this stage completes."/>}</Tabs.Content>
            <Tabs.Content value="quality">{call.quality?<><div className="quality-overview"><div><span className="eyebrow">OVERALL SERVICE QUALITY</span><p>Average of scored dimensions · Language-based assessment</p></div><strong>{call.overall_score?.toFixed(1)??'—'}<small> / 5</small></strong></div><div className="quality-grid">{call.quality.dimensions.map(d=><section className="result-panel" key={d.name}><div className="section-row"><h2 className="capitalize">{d.name}</h2><strong className="dimension-score">{d.score??'—'}<small> / 5</small></strong></div><div className="meter"><i style={{width:`${(d.score??0)*20}%`}}/></div><p>{d.rationale}</p>{d.score===null&&<span className="badge">Insufficient evidence</span>}{evidenceButtons(d.evidence_ids)}</section>)}</div></>:<Empty busy={busy} text="Quality scores will appear after the summary is ready."/>}</Tabs.Content>
            <Tabs.Content value="transcript"><section className="result-panel transcript-panel"><div className="section-row"><h2>The conversation</h2><span className="micro-label">{call.transcript?.length||0} SEGMENTS</span></div><p className="transcript-note">Unknown means the recording did not establish speaker identity.</p>{call.transcript?.length?call.transcript.map(s=><article id={`segment-${s.id}`} tabIndex={-1} key={s.id} className={`segment ${highlight===s.id?'highlighted':''}`}><span className="segment-number">{String(s.id).padStart(2,'0')}</span><div><strong className={s.speaker==='Agent'?'agent-speaker':''}>{s.speaker}</strong><p>{s.text}</p></div></article>):<Empty busy={busy} text="No transcript is available yet."/>}</section></Tabs.Content>
            <Tabs.Content value="activity"><section className="result-panel"><h2>Behind the analysis</h2><p>Stage transitions, provider attempts, and fallback decisions.</p><ol className="activity-list">{call.events?.map((e,i)=><li key={i}><span className="event-dot"/><div><strong className="capitalize">{e.stage}</strong><p>{e.message}</p>{e.model&&<code>{e.model}</code>}</div></li>)}</ol></section></Tabs.Content>
          </Tabs.Root>
        </>}
      </main><footer className="workspace-footer"><ShieldCheck size={13}/> AI supports your judgment. Review evidence before acting.</footer>
    </div>
  </div>
}
function Empty({busy,text}:{busy:boolean,text:string}){return <div className="empty-result" role="status">{busy?<LoaderCircle className="spin"/>:<FileText/>}<p>{text}</p></div>}
