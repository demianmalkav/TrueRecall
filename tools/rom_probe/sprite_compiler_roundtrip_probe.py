#!/usr/bin/env python3
"""Prove the inverse sprite compiler against a simple retail player frame."""
from __future__ import annotations
import argparse,hashlib,sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build'))
from sprite_asset_compiler import compile_frame
EXPECTED_SIZE=2_097_152;EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411';DESC=0x0E51FE;SEL=2

def u16(b,o):return int.from_bytes(b[o:o+2],'big')
def rle128(rom,off):
 out=bytearray();p=off
 while True:
  c=rom[p];p+=1
  if c==0:break
  if c<0x80:n=128-c;out+=rom[p:p+n];p+=n
  else:n=256-c;out+=bytes([rom[p]])*n;p+=1
 assert len(out)==128;return bytes(out)
def chunk(rom,word):
 group=(word>>8)&0x3f;idx=word&0xff;src=int.from_bytes(rom[DESC+2+group*4:DESC+6+group*4],'big')
 if src&0x80000000:
  table=src&0x7fffffff;e=u16(rom,table+idx*2)
  return rle128(rom,table+(e&0x7fff)) if e&0x8000 else rom[table+e:table+e+128]
 return rom[src+idx*128:src+(idx+1)*128]
def pixel(c,t,x,y):
 v=c[t*32+y*4+x//2];return(v>>4)&15 if x%2==0 else v&15
def chunk_img(c):
 im=Image.new('P',(16,16),0);p=im.load()
 for tx in range(2):
  for ty in range(2):
   t=tx*2+ty
   for y in range(8):
    for x in range(8):p[tx*8+x,ty*8+y]=pixel(c,t,x,y)
 return im

def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);a=ap.parse_args();rom=a.rom.read_bytes()
 assert len(rom)==EXPECTED_SIZE and hashlib.sha1(rom).hexdigest()==EXPECTED_SHA1
 enc=u16(rom,DESC+SEL);alias=enc&0x0ffe;ro=u16(rom,DESC+alias);addr=DESC+ro;n=rom[addr+15];retail=rom[addr:addr+0x10+n*4]
 # Known simple retail frame: two aligned chunks, geometry origin=(9,5), clip=16x32.
 assert retail[:16].hex()=='00000000000000090005001000204002'
 im=Image.new('P',(16,32),0)
 for i in range(n):
  p=addr+16+i*4;x=rom[p]-15;y=rom[p+1]-15;word=u16(rom,p+2);im.paste(chunk_img(chunk(rom,word)),(x,y))
 rec,chunks,m=compile_frame(im,origin_x=9,origin_y=5,clip_width=16,clip_height=32,record_flags=0x40,group=0)
 assert rec==retail
 assert chunks[:128]==chunk(rom,0) and chunks[128:256]==chunk(rom,1)
 print('PASS: retail player archetype191 selector2 mapping and chunks recompile byte-identically')
 print(m)
if __name__=='__main__':main()
