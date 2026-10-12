/* Egen statisk fixturserver lever og stopper med akkurat denne testen. */
'use strict';
const http=require('http'),fs=require('fs'),path=require('path');
module.exports=async function(root){
 const base=path.resolve(root),server=http.createServer((request,response)=>{
  let p;try{p=path.resolve(base,'.'+decodeURIComponent(new URL(request.url,'http://localhost').pathname));}catch(e){response.writeHead(400);response.end();return;}
  if(!p.startsWith(base+path.sep)){response.writeHead(403);response.end();return;}
  fs.readFile(p,(error,data)=>{if(error){response.writeHead(404);response.end();return;}const type={'.html':'text/html','.js':'application/javascript','.json':'application/json','.png':'image/png','.wasm':'application/wasm'}[path.extname(p)]||'application/octet-stream';response.writeHead(200,{'Content-Type':type,'Cache-Control':'no-store'});response.end(data);});
 });
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
 return {url:'http://127.0.0.1:'+server.address().port+'/moonstone.html',close:()=>new Promise(resolve=>{server.close(resolve);server.closeAllConnections();})};
};
