import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { runResearchBridge } from './bridge.mjs';
const data=JSON.parse(readFileSync(new URL('./examples-autopsy-access.json',import.meta.url),'utf8'));
const out=runResearchBridge(data);
if(out.status!=='LOCAL_RESEARCH_CONNECTION_SUCCEEDED')throw Error('EXAMPLE_CONNECTION_FAILED');
mkdirSync(new URL('./evidence/',import.meta.url),{recursive:true});
writeFileSync(new URL('./evidence/runtime-example-output.json',import.meta.url),JSON.stringify(out,null,2)+'\n');
writeFileSync(new URL('./evidence/runtime-example-support-draft.txt',import.meta.url),out.research_execution.support_packet.draft_text+'\n');
console.log(JSON.stringify({status:out.status,version:out.research_receipt.adapter_version,
  warnings:out.research_execution.procedural_warnings.map(x=>x.code),
  legacy_status:out.legacy_execution.receipt.status,python_status:out.research_receipt.status,
  production_integration:out.production_integration,total_score:out.research_execution.total_score}));
