#!/usr/bin/env python3
"""Compile sprite art into True Lies mapping records and 16x16 raw chunk banks.

This is the inverse of the recovered retail actor renderer. It deliberately emits
one resource group per invocation and uses aligned 16x16 source cells. Index 0 in
the source palette is transparent.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from PIL import Image

def parse_int(s:str)->int:return int(s,0)

def encode_tile(px,ox:int,oy:int)->bytes:
 out=bytearray()
 for y in range(8):
  for x in range(0,8,2):
   a=px[ox+x,oy+y];b=px[ox+x+1,oy+y]
   if not(0<=a<16 and 0<=b<16):raise ValueError('palette index >15')
   out.append((a<<4)|b)
 assert len(out)==32
 return bytes(out)

def encode_chunk(img:Image.Image,x0:int,y0:int)->bytes:
 cell=Image.new('P',(16,16),0)
 crop=img.crop((x0,y0,min(x0+16,img.width),min(y0+16,img.height)))
 cell.paste(crop,(0,0));px=cell.load()
 # Genesis multi-tile sprite ordering is column-major for a 2x2 tile sprite.
 return b''.join(encode_tile(px,tx*8,ty*8) for tx in range(2) for ty in range(2))

def indexed_image(path:Path,palette_json:Path|None)->Image.Image:
 src=Image.open(path)
 if src.mode=='P' and palette_json is None:
  vals=set(src.getdata())
  if vals and max(vals)>15:raise ValueError('indexed PNG uses indices >15; provide palette JSON for remap')
  return src.copy()
 if palette_json is None:raise ValueError('RGB/RGBA input requires --palette-json with 16 RGB triplets')
 pal=json.loads(palette_json.read_text())
 if len(pal)!=16 or any(len(c)!=3 for c in pal):raise ValueError('palette JSON must be 16 RGB triplets')
 rgba=src.convert('RGBA');out=Image.new('P',rgba.size,0);op=out.load();sp=rgba.load()
 for y in range(rgba.height):
  for x in range(rgba.width):
   r,g,b,a=sp[x,y]
   if a<128:op[x,y]=0;continue
   op[x,y]=min(range(1,16),key=lambda i:(r-pal[i][0])**2+(g-pal[i][1])**2+(b-pal[i][2])**2)
 flat=[]
 for c in pal:flat.extend(c)
 flat += [0]*(768-len(flat));out.putpalette(flat)
 return out

def compile_frame(img:Image.Image,*,origin_x:int,origin_y:int,clip_width:int|None=None,clip_height:int|None=None,
                  control0:int=0,control1:int=0,control2:int=0,record_flags:int=0x40,group:int=0):
 if img.mode!='P':raise ValueError('compile_frame expects indexed P image')
 if not 0<=group<64:raise ValueError('group must be 0..63')
 cw=img.width if clip_width is None else clip_width;ch=img.height if clip_height is None else clip_height
 for name,v in [('origin_x',origin_x),('origin_y',origin_y),('clip_width',cw),('clip_height',ch)]:
  if not 0<=v<=0xffff:raise ValueError(f'{name} out of word range')
 chunks=[];chunk_to_idx={};pieces=[];px=img.load()
 for y in range(0,img.height,16):
  for x in range(0,img.width,16):
   nonzero=any(px[xx,yy] for yy in range(y,min(y+16,img.height)) for xx in range(x,min(x+16,img.width)))
   if not nonzero:continue
   # Retail renderer adds 0x71 before SAT; piece +15 completes the Genesis +0x80 coordinate bias.
   sx=x+15;sy=y+15
   if not(0<=sx<=255 and 0<=sy<=255):raise ValueError('piece coordinate cannot be represented with +15 bias')
   chunk=encode_chunk(img,x,y);idx=chunk_to_idx.get(chunk)
   if idx is None:
    idx=len(chunks)
    if idx>=256:raise ValueError('more than 256 unique chunks in one resource group')
    chunk_to_idx[chunk]=idx;chunks.append(chunk)
   pieces.append((sx,sy,(group<<8)|idx))
 if not pieces:raise ValueError('frame contains no nontransparent pieces')
 if len(pieces)>255:raise ValueError('piece count >255')
 rec=bytearray()
 for v in(control0,control1,control2,origin_x,origin_y,cw,ch):rec+=int(v).to_bytes(2,'big')
 rec+=bytes([record_flags&255,len(pieces)])
 for x,y,w in pieces:rec+=bytes([x,y])+w.to_bytes(2,'big')
 manifest={'width':img.width,'height':img.height,'origin_x':origin_x,'origin_y':origin_y,'clip_width':cw,'clip_height':ch,
  'record_flags':record_flags&255,'piece_count':len(pieces),'unique_chunks':len(chunks),'group':group,
  'pieces':[{'local_x':x-15,'local_y':y-15,'stored_x':x,'stored_y':y,'piece_word':f'0x{w:04X}','chunk_index':w&255} for x,y,w in pieces]}
 return bytes(rec),b''.join(chunks),manifest

def main():
 ap=argparse.ArgumentParser();ap.add_argument('image',type=Path);ap.add_argument('out_prefix',type=Path);ap.add_argument('--palette-json',type=Path)
 ap.add_argument('--origin-x',type=parse_int,required=True);ap.add_argument('--origin-y',type=parse_int,required=True)
 ap.add_argument('--clip-width',type=parse_int);ap.add_argument('--clip-height',type=parse_int)
 ap.add_argument('--control0',type=parse_int,default=0);ap.add_argument('--control1',type=parse_int,default=0);ap.add_argument('--control2',type=parse_int,default=0)
 ap.add_argument('--record-flags',type=parse_int,default=0x40);ap.add_argument('--group',type=parse_int,default=0)
 a=ap.parse_args();img=indexed_image(a.image,a.palette_json)
 rec,chunks,m=compile_frame(img,origin_x=a.origin_x,origin_y=a.origin_y,clip_width=a.clip_width,clip_height=a.clip_height,
  control0=a.control0,control1=a.control1,control2=a.control2,record_flags=a.record_flags,group=a.group)
 a.out_prefix.parent.mkdir(parents=True,exist_ok=True);a.out_prefix.with_suffix('.mapping.bin').write_bytes(rec);a.out_prefix.with_suffix('.chunks.bin').write_bytes(chunks);a.out_prefix.with_suffix('.json').write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps(m,indent=2))
if __name__=='__main__':main()
