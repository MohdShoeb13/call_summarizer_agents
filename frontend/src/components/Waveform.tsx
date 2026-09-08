export function Waveform({compact=false}:{compact?:boolean}) {
  return <div className={`waveform ${compact?'waveform-compact':''}`} aria-hidden="true"><div className="wave-glow"/><div className="wave-bars">{Array.from({length:compact?46:112},(_,i)=>{
    const count=compact?46:112; const x=i/count; const envelope=Math.sin(x*Math.PI)**1.3
    const height=8+envelope*(24+Math.abs(Math.sin(i*1.73))*110+Math.abs(Math.cos(i*.29))*75)
    return <i key={i} style={{height:`${height}px`,animationDelay:`${-i*.13}s`,animationDuration:`${2.1+(i%9)*.17}s`}}/>
  })}</div><div className="wave-axis"/></div>
}
