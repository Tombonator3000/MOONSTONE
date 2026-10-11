/* Felles browser-canvas-kjerne for pakking og meningsfulle koordinattester. */
'use strict';
module.exports=async({raw,source,w,h,composite,scale,placement,source_clip,clip,ink_indices,ink_rect,paths,palette})=>{
    const read=async data=>{const im=new Image();im.src='data:image/png;base64,'+data;await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;c.getContext('2d').drawImage(im,0,0);return c;};
    const original=await read(source),master=await read(raw);
    const bounds=c=>{const pix=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let x0=c.width,y0=c.height,x1=0,y1=0;
     for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(pix[(y*c.width+x)*4+3]>=16){x0=Math.min(x0,x);x1=Math.max(x1,x+1);y0=Math.min(y0,y);y1=Math.max(y1,y+1);}
     if(x1<=x0||y1<=y0)throw Error('Tom rasterkilde');return[x0,y0,x1-x0,y1-y0];};
    const from=bounds(master),to=bounds(original),out=document.createElement('canvas');out.width=w;out.height=h;
    const contain=Math.min(w/from[2],h/from[3]);
    const dest=composite?[0,0,composite.width*scale,composite.height*scale]:placement==='contain'?[(w-from[2]*contain)/2,h-from[3]*contain,from[2]*contain,from[3]*contain]:[to[0]*w/original.width,to[1]*h/original.height,to[2]*w/original.width,to[3]*h/original.height];
    const ctx=out.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
    if(composite){
     // Tegn samme fullmaster foer CEL-utklipp. Felles skalering unngaar nye soemmer.
     const full=document.createElement('canvas');full.width=composite.width*scale;full.height=composite.height*scale;
     const fc=full.getContext('2d');fc.imageSmoothingEnabled=true;fc.imageSmoothingQuality='high';fc.drawImage(master,...from,...dest);
     ctx.imageSmoothingEnabled=false;ctx.drawImage(full,...composite.rect.map(v=>v*scale),0,0,w,h);
    }else ctx.drawImage(master,...from,...dest);
    if(source_clip){
     const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(scale,scale);mc.fill(new Path2D(clip),'evenodd');
     ctx.save();ctx.globalCompositeOperation='destination-in';ctx.drawImage(mask,0,0);ctx.restore();
    }
    if(ink_indices?.length){
     ctx.save();ctx.scale(scale,scale);ctx.beginPath();ctx.rect(...ink_rect);ctx.clip();ctx.clip(new Path2D(clip),'evenodd');
     for(const index of ink_indices){ctx.fillStyle='rgb('+palette[index].slice(0,3).join(',')+')';for(const path of paths.filter(p=>p.index===index))ctx.fill(new Path2D(path.d),'evenodd');}
     ctx.restore();
    }
    const ref=document.createElement('canvas');ref.width=w;ref.height=h;ref.getContext('2d').drawImage(original,0,0,w,h);
    const aa=ctx.getImageData(0,0,w,h).data,bb=ref.getContext('2d').getImageData(0,0,w,h).data;
    let both=0,either=0,ink=0;for(let i=3;i<aa.length;i+=4){const a=aa[i]>=128,b=bb[i]>=128;both+=a&&b;either+=a||b;ink+=a;}
    return{png:out.toDataURL('image/png').split(',')[1],master_size:[master.width,master.height],source_size:[original.width,original.height],raw_ink_bounds:from,target_ink_bounds:dest,
     silhouette_iou:both/either,opaque_pixels:ink,texture_size:[w,h]};
   };
