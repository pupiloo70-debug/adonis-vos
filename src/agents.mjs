import { createHash } from 'node:crypto';
import { analyzeProject, VERSION } from './project.mjs';
// A bounded local coordinator; external LLM connections remain manual.
const digest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const CAPABILITIES=['SOURCE_REVIEW','COUNTEREXAMPLE_REVIEW','LOCAL_RULE_EVALUATION'];
export class CentralCore {
  #agents=new Map(); #tasks=new Map(); #limits;
  constructor({maxAgents=4,maxTasks=16}={}) {
    if(!Number.isSafeInteger(maxAgents)||maxAgents<1||maxAgents>8||!Number.isSafeInteger(maxTasks)||maxTasks<1||maxTasks>100)throw Error('INVALID_LIMITS');
    this.#limits={maxAgents,maxTasks};
  }
  register(agent) {
    if(!agent||typeof agent.id!=='string'||!agent.id.trim()||this.#agents.has(agent.id))throw Error('INVALID_AGENT');
    if(this.#agents.size>=this.#limits.maxAgents)throw Error('AGENT_LIMIT');
    if(!['INTENT_RECEIVED','LOCAL_ADAPTER_CONFIGURED'].includes(agent.connection))throw Error('INVALID_CONNECTION');
    if(!['BELIEF_NARRATIVE','DESIGN','EXECUTION'].includes(agent.layer))throw Error('INVALID_LAYER');
    if(!Array.isArray(agent.capabilities)||agent.capabilities.some(c=>!CAPABILITIES.includes(c)))throw Error('INVALID_CAPABILITY');
    if(agent.connection==='LOCAL_ADAPTER_CONFIGURED'&&(agent.layer!=='EXECUTION'||typeof agent.runtime_ref!=='string'||!agent.runtime_ref.trim()))throw Error('RUNTIME_EVIDENCE_REQUIRED');
    this.#agents.set(agent.id,structuredClone({...agent,state:'ACTIVE'}));
  }
  assign({id,agent_id,capability}) {
    const a=this.#agents.get(agent_id);
    if(!a||a.state!=='ACTIVE')throw Error('AGENT_UNAVAILABLE');
    if(a.connection!=='LOCAL_ADAPTER_CONFIGURED')throw Error('INTENT_IS_NOT_RUNTIME');
    if(!a.capabilities.includes(capability))throw Error('CAPABILITY_DENIED');
    if(typeof id!=='string'||!id.trim()||this.#tasks.has(id))throw Error('INVALID_TASK');
    if(this.#tasks.size>=this.#limits.maxTasks)throw Error('TASK_LIMIT');
    this.#tasks.set(id,{id,agent_id,capability,state:'ASSIGNED_NOT_EXECUTED'});
  }
  suspend(id) {
    const a=this.#agents.get(id);if(!a)throw Error('AGENT_UNAVAILABLE');a.state='SUSPENDED';
    for(const t of this.#tasks.values())if(t.agent_id===id&&t.state==='ASSIGNED_NOT_EXECUTED')t.state='ON_HOLD';
  }
  runLocal(id,project) {
    const t=this.#tasks.get(id),a=t&&this.#agents.get(t.agent_id);
    if(!t||t.state!=='ASSIGNED_NOT_EXECUTED'||a?.state!=='ACTIVE')throw Error('TASK_NOT_RUNNABLE');
    if(t.capability!=='LOCAL_RULE_EVALUATION'||a.runtime_ref!=='src/project.mjs')throw Error('LOCAL_ADAPTER_NOT_SUPPORTED');
    try {
      const result=analyzeProject(project);
      const receipt={task_id:id,agent_id:a.id,adapter_version:VERSION,input_sha256:digest(project),output_sha256:digest(result),executed_at:new Date().toISOString(),status:'SUCCEEDED',environment:'CALLING_NODE_PROCESS'};
      t.state='SUCCEEDED';t.receipt=receipt;
      return {result,receipt:structuredClone(receipt)};
    } catch(e){t.state='FAILED';throw e;}
  }
  snapshot(){return structuredClone({agents:[...this.#agents.values()],tasks:[...this.#tasks.values()],limits:this.#limits,external_api_calls:0,dispatch_mode:'BUILTIN_LOCAL_ONLY'});}
}
