#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
from PIL import Image
TOOLS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLS/'build'))
sys.path.insert(0,str(TOOLS))
from sprite_sequence_compiler import compile_sequence
from sprite_frame_export import u16,resolve_chunk,chunk_image
EXPECTED='d39174bed46ede85531b86df7ba49123ce2f8411'; DESC=0x0E51FE; SELECTORS=[2,258,260,262]

def retail_frame(rom,selector):
    enc=u16(rom,DESC+selector);alias=enc&0x0FFE;ro=u16(rom,DESC+alias);addr=DESC+ro;n=rom[addr+15]
    pcs=[]
    for i in range(n):
        p=addr+16+i*4;x=rom[p]-15;y=rom[p+1]-15;w=u16(rom,p+2);pcs.append((x,y,w,resolve_chunk(rom,DESC,w)))
    minx=min(x for x,_,_,_ in pcs);miny=min(y for _,y,_,_ in pcs);maxx=max(x+16 for x,_,_,_ in pcs);maxy=max(y+16 for _,y,_,_ in pcs)
    assert minx>=0 and miny>=0 and all(x%16==0 and y%16==0 for x,y,_,_ in pcs),(selector,pcs)
    img=Image.new('P',(maxx,maxy),0);pal=[]
    for i in range(256):pal.extend((i,i,i))
    img.putpalette(pal)
    for x,y,w,ch in pcs: img.paste(chunk_image(ch,bool(w&0x4000),bool(w&0x8000)),(x,y))
    hdr=[u16(rom,addr+i*2) for i in range(7)];flags=rom[addr+14]
    return img,dict(origin_x=hdr[3],origin_y=hdr[4],clip_width=hdr[5],clip_height=hdr[6],control0=hdr[0],control1=hdr[1],control2=hdr[2],record_flags=flags)

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);a=ap.parse_args();rom=a.rom.read_bytes();assert hashlib.sha1(rom).hexdigest()==EXPECTED
    frames=[];src=[]
    for sel in SELECTORS:
        img,h=retail_frame(rom,sel);row=dict(h);row['image']=img;frames.append(row);src.append((sel,img))
    records,chunks,meta=compile_sequence(frames,group=0)
    for (sel,orig),rec in zip(src,records):
        n=rec[15];canvas=Image.new('P',orig.size,0);canvas.putpalette(orig.getpalette())
        for i in range(n):
            p=16+i*4;x=rec[p]-15;y=rec[p+1]-15;w=int.from_bytes(rec[p+2:p+4],'big');idx=w&0xff;ch=chunks[idx*128:(idx+1)*128];canvas.paste(chunk_image(ch,bool(w&0x4000),bool(w&0x8000)),(x,y))
        assert canvas.tobytes()==orig.tobytes(),f'pixel mismatch selector {sel}'
    assert meta['frame_count']==4
    assert meta['global_unique_chunks']==6 and meta['total_chunk_bytes']==768
    assert meta['max_frame_working_set']==2
    assert meta['max_scanline_pieces']==1 and meta['max_scanline_pixels']==16
    assert meta['max_transition_new_chunks']==2 and meta['loop_new_chunks']==2
    assert [f['unique_chunks_in_frame'] for f in meta['frames']]==[2,2,2,2]
    print('PASS sequence compiler pixel-roundtrip selectors',SELECTORS)
    print(meta)
if __name__=='__main__':main()
