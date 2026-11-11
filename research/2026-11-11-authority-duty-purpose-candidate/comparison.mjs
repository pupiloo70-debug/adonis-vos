import { evaluate as oldEvaluate } from './authority-duty.original.mjs';
import { evaluate as newEvaluate } from './authority-duty.mjs';
const at = '2026-11-09T06:00:00Z';
function e(id,type,source_ref){return {id,type,source_ref,at,case_id:'SYN-TIME',actor_id:'CONTROLLER-X',question_id:'Q-ONE'};}
const request = {...e('REQ','REQUEST_RECEIVED','SRC-REQUEST'),at:'2026-11-08T00:00:00Z'};
const base = {synthetic:true,case_id:'SYN-TIME',actor_id:'CONTROLLER-X',question_id:'Q-ONE',now:'2026-11-10T00:00:00Z',duty:{basis_status:'UNKNOWN',deadline_status:'UNKNOWN'},events:[],residual_questions:['verification outcome contested'],past_burden:[{type:'previous burden',amount:null}]};
const paired = (idV,idR) => ({...base,events:[request,e(idV,'CORE_ACCESS_VERIFIED','SRC-V'),e(idR,'REFUSAL','SRC-R')]});
const out=[];
for(const [name,input] of [['verified_id_E2',paired('E2','E3')],['verified_id_E3',paired('E3','E2')]]) {
 const a = oldEvaluate(input),b = newEvaluate(input);
 out.push({name,input_events:input.events.map(({id,type,at,source_ref})=>({id,type,at,source_ref})),before:{status:a.duty_fulfillment_status,omission_review:a.omission_review,explanation_created:!!a.explanation_task},after:{status:b.duty_fulfillment_status,omission_review:b.omission_review,explanation_created:!!b.explanation_task,accepted_event_ids:b.accepted_events.map(x=>x.id),prior_burdens_preserved:b.past_burden.length,source_truth_verified:b.source_truth_verified,total_score:b.total_score}});
}
console.log(JSON.stringify(out,null,2));
