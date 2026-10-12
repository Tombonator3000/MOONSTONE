/* Egen kortvarig HTTP-vert for én kampprøve; ingen delt serverprosess. */
'use strict';
const fs=require('fs'),http=require('http'),path=require('path');
const html=fs.readFileSync(process.env.MOONSTONE_PRIVATE_HTML||path.join(__dirname,'runtime-host/moonstone.html'));
const server=http.createServer((req,res)=>{if(req.method==='GET'&&req.url==='/moonstone.html'){res.writeHead(200,{'content-type':'text/html; charset=utf-8','cache-control':'no-store'});res.end(html);}else{res.writeHead(404);res.end();}});
server.listen(0,'127.0.0.1',()=>{process.env.MOONSTONE_URL='http://127.0.0.1:'+server.address().port+'/moonstone.html';server.unref();require(path.join(__dirname,process.env.MOONSTONE_RUNTIME_SCRIPT||'runtime.cjs'));});
