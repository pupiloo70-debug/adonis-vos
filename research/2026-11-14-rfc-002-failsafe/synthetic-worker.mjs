import {parentPort, workerData} from 'node:worker_threads';
// This worker only simulates bridge outcomes. It does not invoke any VOS core.
switch(workerData.scenario){
  case 'HANG': setInterval(()=>{},1000); break;
  case 'THROW': throw new Error('Synthetic module exception');
  case 'CONFLICT': parentPort.postMessage({status:'VERIFIED'}); break;
  default: parentPort.postMessage({status:'READY_FOR_HUMAN_VERIFICATION'});
}
