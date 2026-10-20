'use strict';
const keyFile=document.querySelector('#key-file'),keyInput=document.querySelector('#key'),fileStatus=document.querySelector('#file-error'),submit=document.querySelector('button[type="submit"]');
let selection=0;
keyFile.addEventListener('change',async()=>{
  const current=++selection,file=keyFile.files[0];
  if(!file){fileStatus.textContent='No file was selected. Choose the operator.key file, or paste its contents into Operator key.';return;}
  keyInput.value='';
  submit.disabled=true;
  fileStatus.dataset.state='reading';
  fileStatus.textContent='Reading '+file.name+'…';
  try{
    if(file.size>256)throw Error('Choose the small operator.key file, not a folder or backup.');
    const value=(await file.text()).trim();
    if(current!==selection)return;
    if(!/^[A-Za-z0-9_-]{32,128}$/.test(value))throw Error('This file does not contain an operator key. Choose operator.key or paste the key into the field above.');
    keyInput.value=value;
    keyInput.dispatchEvent(new Event('input',{bubbles:true}));
    keyInput.dispatchEvent(new Event('change',{bubbles:true}));
    fileStatus.dataset.state='ready';
    fileStatus.textContent='Key loaded from '+file.name+'. Click Open workspace to sign in.';
  }catch(error){
    if(current!==selection)return;
    fileStatus.dataset.state='error';
    fileStatus.textContent=error.name==='NotReadableError'?'Chrome could not read that file. Open it locally and paste its contents into Operator key.':error.message;
  }finally{if(current===selection)submit.disabled=false;}
});
keyFile.addEventListener('cancel',()=>{
  if(keyInput.value)return;
  fileStatus.dataset.state='error';
  fileStatus.textContent='Chrome did not select a file. Choose operator.key and confirm Open in the file picker, or paste the key into the field above.';
});
