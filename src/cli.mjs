import { readFile, writeFile, stat } from 'node:fs/promises';
import { resolve } from 'node:path';
import { importProject, analyzeProject, MAX_BYTES } from './project.mjs';
const [input,output]=process.argv.slice(2);
if(!input) { console.error('Usage: node src/cli.mjs input.json [output.json]'); process.exitCode=2; }
else {
  try {
    if(output&&resolve(input)===resolve(output))throw Error('INPUT_OVERWRITE_DENIED');
    if((await stat(input)).size>MAX_BYTES)throw Error('IMPORT_SIZE_OR_TYPE');
    const result=JSON.stringify(analyzeProject(importProject(await readFile(input,'utf8'))),null,2)+'\n';
    if(output)await writeFile(output,result,{flag:'wx'});else process.stdout.write(result);
  } catch(e){console.error('VOS_INPUT_OR_OUTPUT_ERROR: '+e.message);process.exitCode=1;}
}
