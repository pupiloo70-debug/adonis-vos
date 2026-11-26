import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createSyntheticValidator} from './caselaw-validator.mjs';
import {record,citation} from './fixture.mjs';
const attacks=[['fabricated ID',{id:'SYNTH-999'},{}],['wrong court',{court:'OTHER'},{}],['wrong date',{date:'2001-01-01'},{}],['wrong jurisdiction',{jurisdiction:'OTHER'},{}],['wrong procedure',{procedure:'OTHER'},{}],['wrong issue',{issue:'OTHER'},{}],['fabricated quotation',{quote:'Invented holding'},{}],['unsupported proposition',{proposition:'Automatic immunity'},{}],['missing dissent',{dissent:null},{}],['summary only',{}, {access:'SUMMARY'}],['changed source bytes',{}, {text:'Changed'}],['stale status',{}, {currentness:'UNKNOWN'}],['party argument',{}, {role:'PARTY_ARGUMENT'}]];
for(const [name,c,r] of attacks)test(name,()=>{const out=createSyntheticValidator([{...record,...r}])([{...citation,...c},citation]);assert.equal(out.results[0].status,'BLOCKED');assert.equal(out.real_citation_authorized,false);assert.equal(out.total_score,null);});
test('valid synthetic match preserved with invalid sibling',()=>{const out=createSyntheticValidator([record])([citation,{...citation,id:'missing'}]);assert.equal(out.results[0].status,'SYNTHETIC_MATCH_ONLY');assert.equal(out.results[1].status,'BLOCKED');assert.equal(out.real_citation_authorized,false);});
test('ambiguous registry blocks',()=>assert.equal(createSyntheticValidator([record,record])([citation]).results[0].status,'BLOCKED'));
test('caller cannot override registry',()=>{const records=[structuredClone(record)];const run=createSyntheticValidator(records);records[0].role='PARTY_ARGUMENT';assert.equal(run([citation]).results[0].status,'SYNTHETIC_MATCH_ONLY');});
