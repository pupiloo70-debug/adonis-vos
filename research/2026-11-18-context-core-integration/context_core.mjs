// Opt-in composition; no default CLI, upstream core or P02 source changes.
import { createHash } from 'node:crypto';
import { runIntegratedCore } from '../0.2-core-guard-integration.v2/core_guard.mjs';
import { reviewContextIsolated } from './p02/testimony-controller.mjs';
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
export function runContextCore(input){
 const x=structuredClone(input);
 if(!obj(x)||!obj(x.core)||!obj(x.context)||!obj(x.binding))throw Error('EXPLICIT_CONTEXT_ENVELOPE_REQUIRED');
 if(x.context.synthetic!==true||x.core.project?.synthetic!==true||x.core.legacy_project?.synthetic!==true)throw Error('SYNTHETIC_ONLY');
 const scope=['case_id','track_id','subject_id'];
 if(scope.some(k=>typeof x.core.project[k]!=='string'||!x.core.project[k]||x.binding[k]!==x.core.project[k])||x.context.case_id!==x.binding.case_id)throw Error('CONTEXT_SCOPE_CONFLICT');
 if(['track_id','subject_id'].some(k=>Object.hasOwn(x.context,k)&&x.context[k]!==x.binding[k]))throw Error('CONTEXT_SCOPE_CONFLICT');
 const ids=x.core.project.support_reviews?.map(r=>r.id);
 if(!Array.isArray(ids)||new Set(ids).size!==ids.length||!Array.isArray(x.binding.items))throw Error('AMBIGUOUS_REVIEW_BINDING');
 const mapped=new Set();
 for(const collection of ['statements','records','remedies']){
  if(!Array.isArray(x.context[collection]))throw Error('CONTEXT_COLLECTION_REQUIRED');
  for(const row of x.context[collection]){
   if(!obj(row)||typeof row.id!=='string'||!row.id)throw Error('EXPLICIT_ITEM_ID_REQUIRED');
   const key=JSON.stringify([collection,row.id]);
   if(mapped.has(key))throw Error('AMBIGUOUS_ITEM_BINDING');mapped.add(key);
   const pairs=x.binding.items.filter(p=>p?.collection===collection&&p.item_id===row.id);
   if(pairs.length!==1||!ids.includes(pairs[0].review_id)||(row.review_id!=null&&row.review_id!==pairs[0].review_id))throw Error('ITEM_REVIEW_BINDING_CONFLICT');
  }
 }
 if(mapped.size!==x.binding.items.length)throw Error('ORPHAN_ITEM_BINDING');
 const core=runIntegratedCore(x.core);
 const contextInput={...x.context,subject_id:x.binding.subject_id};
 let context;
 try{context=reviewContextIsolated(contextInput);}
 catch(error){return {status:'PARTIAL_CONTEXT_STAGE_FAILURE',core,context:null,context_failure:String(error.message),binding:x.binding,total_score:null,production_integration:false};}
 // Preserve original core result and P02 payload intact; no independent-verification promotion.
 const status=core.status==='LOCAL_INTEGRATION_SUCCEEDED'?(context.isolation_report.held.length?'CONTEXT_INTEGRATION_WITH_HELD_ITEMS':'LOCAL_CONTEXT_INTEGRATION_SUCCEEDED'):'PARTIAL_CORE_STAGE_RESULT';
 return {schema:'ADONIS-CONTEXT-CORE/OPT-IN-1',status,core,context,binding:x.binding,
  receipts:{context:{status:'SUCCEEDED',input_sha256:sha(contextInput),output_sha256:sha(context)}},
  total_score:null,production_integration:false,default_cli_changed:false,external_execution:false};
}
