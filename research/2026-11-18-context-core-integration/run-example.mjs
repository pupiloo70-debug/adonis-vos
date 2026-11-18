import {readFileSync} from 'node:fs';import {runContextCore} from './context_core.mjs';
const core=JSON.parse(readFileSync(new URL('../0.2-core-guard-integration.v2/synthetic-input.json',import.meta.url)));
const context=JSON.parse(readFileSync(new URL('./p02/synthetic-fixture.json',import.meta.url)));context.case_id=core.project.case_id;
const binding={case_id:core.project.case_id,track_id:core.project.track_id,subject_id:core.project.subject_id,items:[]};
for(const collection of ['statements','records','remedies'])for(const row of context[collection])binding.items.push({collection,item_id:row.id,review_id:core.project.support_reviews[0].id});
const result=runContextCore({core,context,binding});console.log(JSON.stringify(result,null,2));if(result.status!=='LOCAL_CONTEXT_INTEGRATION_SUCCEEDED')process.exitCode=1;
