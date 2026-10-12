/* Regenerer og hashkontroller originalreferansen foer den frosne runtimeporten. */
'use strict';
const path=require('path'),{spawnSync}=require('child_process');
const result=spawnSync('python3',[path.join(__dirname,'regenerate-shadow-reference-v1.py')],{stdio:'inherit'});
if(result.status!==0)throw Error('Original skyggereferanse kunne ikke verifiseres');
require('./runtime-retention-fixtures-v4.cjs');
