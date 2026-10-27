import { useEffect, useRef, useState, type ReactNode } from 'react';
import { X, ArrowUpRight, FileSpreadsheet, FileText, LoaderCircle, Check, AlertTriangle } from 'lucide-react';
import { type Json } from './api';
export function Logo({small=false}:{small?:boolean}) {return <span className={'brand '+(small?'small':'')}><span className="brand-symbol"><i/><i/><i/></span>{!small&&'insyvera'}{!small&&<span className="brand-dot">✧</span>}</span>}
export function Spinner(){return <LoaderCircle size={18} className="spin"/>}
export function Badge({children,tone='green'}:{children:ReactNode,tone?:string}){return <span className={'badge '+tone}>{children}</span>}
export function FileIcon({type}:{type:string}) {return <span className={'file-icon '+type}>{['xlsx','csv'].includes(type)?<FileSpreadsheet size={21}/>:<FileText size={21}/>}</span>}
export function Empty({title,detail,action}:{title:string,detail:string,action?:ReactNode}){return <div className="empty"><span className="empty-orbit"><FileText size={25}/></span><h3>{title}</h3><p>{detail}</p>{action}</div>}
export function Panel({children,title,action,className=''}:{children:ReactNode,title?:string,action?:ReactNode,className?:string}){return <section className={'panel '+className}>{title&&<div className="panel-head"><h3>{title}</h3>{action}</div>}{children}</section>}
export function Modal({title,children,onClose,wide=false}:{title:string,children:ReactNode,onClose:()=>void,wide?:boolean}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const el=ref.current!;el.showModal();return()=>el.close()},[]);
 return <dialog ref={ref} className={'modal '+(wide?'wide':'')} onCancel={onClose} onClick={e=>{if(e.target===ref.current)onClose()}}><div className="modal-head"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={20}/></button></div>{children}</dialog>
}
export function Chart({chart}:{chart:Json}){
 const ref=useRef<HTMLDivElement>(null);const [failed,setFailed]=useState(false);
 useEffect(()=>{let disposed=false; let plot:any;
 import('plotly.js-basic-dist-min').then(module=>{plot=module.default;if(disposed)return;
 return plot.newPlot(ref.current,chart.data,{...chart.layout,autosize:true,height:300,paper_bgcolor:'transparent',plot_bgcolor:'transparent',
 margin:{l:45,r:15,t:20,b:55},font:{family:'Inter, Segoe UI, sans-serif',size:11,color:'#737d73'},
 xaxis:{...chart.layout?.xaxis,showgrid:false,zeroline:false},yaxis:{...chart.layout?.yaxis,gridcolor:'#e9ece5',zeroline:false}},
 {responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']})}).catch(()=>setFailed(true));
 const observer=new ResizeObserver(()=>{if(plot&&ref.current)plot.Plots.resize(ref.current)});if(ref.current)observer.observe(ref.current);
 return()=>{disposed=true;observer.disconnect();if(plot&&ref.current)plot.purge(ref.current)}},[chart]);
 return <div className="chart" role="img" aria-label={chart.title}>{failed?<p>Chart could not load. The computed values remain available in the analysis table.</p>:<div ref={ref}/>}</div>
}
export function Status({value}:{value:string}){return <Badge tone={['ready','completed','supported_extract','computed'].includes(value)?'green':['failed','unsupported'].includes(value)?'red':'neutral'}>{['ready','completed','supported_extract','computed'].includes(value)?<Check size={12}/>:value==='failed'?<AlertTriangle size={12}/>:null}{value.replaceAll('_',' ')}</Badge>}
export function TextLink({children,onClick}:{children:ReactNode,onClick:()=>void}){return <button className="text-link" onClick={onClick}>{children}<ArrowUpRight size={14}/></button>}
export function DataTable({columns,rows,limit=100}:{columns:string[],rows:Json[],limit?:number}){return <div className="table-scroll"><table><thead><tr>{columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{rows.slice(0,limit).map((r,i)=><tr key={i}>{columns.map(c=><td key={c}>{r[c]===null||r[c]===undefined?<span className="muted">—</span>:String(r[c])}</td>)}</tr>)}</tbody></table>{rows.length>limit&&<p className="table-note">Showing {limit} of {rows.length} rows. Download the original for the full source.</p>}</div>}
