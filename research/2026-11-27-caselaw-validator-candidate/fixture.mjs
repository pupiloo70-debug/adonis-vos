import {sha256} from './caselaw-validator.mjs';
export const record={id:'SYNTH-001',court:'SYNTHETIC_COURT',date:'2000-01-01',jurisdiction:'SYNTH',procedure:'DOCUMENT_REVIEW',issue:'SOURCE_ACCESS',text:'Synthetic holding: review remains open. Synthetic dissent: scope disputed.',holding:'Synthetic holding: review remains open.',proposition:'Review remains open',role:'COURT_HOLDING',access:'FULL_TEXT',currentness:'CHECKED_SYNTHETIC',dissentRequired:true,dissent:'Scope disputed'};
record.sha256=sha256(record.text);
export const citation={id:record.id,court:record.court,date:record.date,jurisdiction:record.jurisdiction,procedure:record.procedure,issue:record.issue,quote:record.holding,proposition:record.proposition,dissent:record.dissent};
