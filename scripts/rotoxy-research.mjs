#!/usr/bin/env node
// Local operator bridge. Credentials stay inside ROTOXY's encrypted store.
import {readFile, mkdir, writeFile, appendFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {homedir} from 'node:os';
const runtime=process.env.ROTOXY_RUNTIME || resolve(homedir(),'.local/share/rotoxy');
const {StateStore}=await import(pathToFileURL(resolve(runtime,'dist/store.js')));
const {createLightSprintMcpClient}=await import(pathToFileURL(resolve(runtime,'dist/providers/lightsprint-jobs.js')));
const dir=resolve(process.env.OSINTNET_DISPATCH_DIR||'private/discovery'); await mkdir(dir,{recursive:true,mode:0o700});
const store=new StateStore(), state=await store.load();
const cfg=JSON.parse(await readFile(resolve(store.dir,'supervisor.json'),'utf8'));
const sessions=cfg.projects.flatMap(p=>p.registeredSessions).filter((x,i,a)=>a.findIndex(y=>y.accountId===x.accountId)===i).slice(0,4);
const parse=r=>r.structuredContent || JSON.parse(r.content.find(x=>x.type==='text').text);
async function api(s,method,path,body){
 const a=state.accounts.find(a=>a.id===s.accountId && a.enabled); if(!a)throw Error('account_disabled');
 const c=createLightSprintMcpClient({endpoint:new URL(state.config.upstreamUrl),token:await store.revealToken(a),fetch,timeoutMs:25000});
 try{const r=await c.request('tools/call',{name:'lightsprint_api',arguments:{method,path:`/api/workspaces/${s.workspaceId}${path}`,...(body?{body}:{})}}); if(r.isError)throw Error('provider_rejected');return parse(r);}finally{c.close();}
}
const briefsPath=process.argv[3];if(!briefsPath)throw Error('briefs_json_path_required');
const briefs=JSON.parse(await readFile(briefsPath,'utf8'));
if(!Array.isArray(briefs)||briefs.length>sessions.length||briefs.some(b=>!Array.isArray(b)||typeof b[0]!=='string'||! /^[a-z0-9-]{1,40}$/.test(b[0])||typeof b[1]!=='string'))throw Error('invalid_bounded_briefs');
const assignmentDate=new Date().toISOString().slice(0,10);
const mode=process.argv[2] || 'status';
if(mode==='dispatch'){
 for(let i=0;i<briefs.length;i++){
  const [lane,brief]=briefs[i],s=sessions[i],file=resolve(dir,`${lane}.json`);
  try{await readFile(file);console.log(JSON.stringify({lane,skipped:'durable_receipt_exists'}));continue;}catch(e){if(e.code!=='ENOENT')throw e;}
  const before=await api(s,'GET',`/agent-sessions/${s.sessionId}/status`);
  if(before.status?.sessionStatus!=='idle'||before.status?.canSendMessage!==true){console.log(JSON.stringify({lane,skipped:'session_not_idle'}));continue;}
  const marker=`OSINTNET_DISCOVERY_${lane.toUpperCase().replaceAll('-','_')}_DONE`;
  const instructions=`New isolated OSINTNET research assignment, ${assignmentDate}. Supersedes no unfinished repository work: perform TEXT-ONLY research, do not edit any repo, push, create PR, contact anyone, install software, access private records, purchase or change billing. User authorizes economical bounded research. Scope: ${brief}\nBudget: one response, at most 8 web/tool calls, <=6 minutes, <=0.50 USD existing prepaid LightSprint credits; stop early if budget unavailable. No native Codex/Claude subscription calls. Output <=7500 characters: JSON object {lane,observed_at,sources:[{url,issuer,observed_fact,limitation}],recommendations,alternatives,rejected,unknowns,tests}. Distinguish verified facts from proposals. Primary sources only; no invented results. Completion marker on its own line: ${marker}`;
  const receipt={lane,session:s,marker,instructions,started_at:new Date().toISOString(),lease_seconds:600,budget_usd:0.5,cost_before:before.status?.aiGatewaySessionCostUsd,status:'dispatching'};
  await writeFile(file,JSON.stringify(receipt,null,2),{mode:0o600,flag:'wx'});
  try{receipt.dispatch=await api(s,'POST',`/agent-sessions/${s.sessionId}/chat`,{message:instructions,clientMessageId:`osintnet-discovery-${assignmentDate}-${lane}`});receipt.status='accepted';}catch(e){receipt.status='ambiguous';receipt.error=e.name;}
  await writeFile(file,JSON.stringify(receipt,null,2),{mode:0o600});
  await appendFile(resolve(dir,'events.jsonl'),JSON.stringify({at:new Date().toISOString(),lane,status:receipt.status})+'\n',{mode:0o600});
  console.log(JSON.stringify({lane,status:receipt.status}));
 }
}else{
 for(const [lane]of briefs){
  let r;try{r=JSON.parse(await readFile(resolve(dir,`${lane}.json`),'utf8'));}catch{continue;}
  const status=await api(r.session,'GET',`/agent-sessions/${r.session.sessionId}/status`),st=status.status;
  const delta=st?.aiGatewaySessionCostUsd-r.cost_before;
  const transcript=await api(r.session,'GET',`/agent-sessions/${r.session.sessionId}/transcript?limit=100&include=text&maxBytes=131072`);
  await writeFile(resolve(dir,`${lane}-observation.json`),JSON.stringify({observed_at:new Date().toISOString(),status,transcript},null,2),{mode:0o600});
  const items=transcript.items || transcript.messages || [], completed=items.some(x=>x.type==='assistant_snapshot'&&Date.parse(x.time)>=Date.parse(r.started_at)&&JSON.stringify(x.payload).includes(r.marker));
  if(!completed&&st?.canCancelPrompt&&(delta>=r.budget_usd||Date.now()-Date.parse(r.started_at)>r.lease_seconds*1000)){await api(r.session,'POST',`/agent-sessions/${r.session.sessionId}/cancel`,{});console.log(JSON.stringify({lane,state:'cancel_requested',cost_delta:delta}));}
  else console.log(JSON.stringify({lane,state:st?.sessionStatus,model:st?.model,cost_delta:delta,completed}));
 }
}
