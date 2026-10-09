#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from PIL import Image
from sprite_asset_compiler import indexed_image, encode_chunk

def compile_sequence(frames, *, group:int=0):
    if not 0<=group<64: raise ValueError('group must be 0..63')
    chunks=[]; chunk_to_idx={}; records=[]; manifests=[]
    for fi,frame in enumerate(frames):
        img=frame['image']
        if img.mode!='P': raise ValueError('all images must be indexed P')
        ox=int(frame['origin_x']); oy=int(frame['origin_y'])
        cw=int(frame.get('clip_width',img.width)); ch=int(frame.get('clip_height',img.height))
        c0=int(frame.get('control0',0)); c1=int(frame.get('control1',0)); c2=int(frame.get('control2',0)); flags=int(frame.get('record_flags',0x40))&0xff
        pieces=[]; px=img.load(); used=[]
        for y in range(0,img.height,16):
            for x in range(0,img.width,16):
                nonzero=any(px[xx,yy] for yy in range(y,min(y+16,img.height)) for xx in range(x,min(x+16,img.width)))
                if not nonzero: continue
                sx=x+15; sy=y+15
                if not(0<=sx<=255 and 0<=sy<=255): raise ValueError('piece coordinate out of byte range')
                chunk=encode_chunk(img,x,y); idx=chunk_to_idx.get(chunk)
                if idx is None:
                    idx=len(chunks)
                    if idx>=256: raise ValueError('sequence exceeds 256 unique chunks in one group')
                    chunk_to_idx[chunk]=idx; chunks.append(chunk)
                pieces.append((sx,sy,(group<<8)|idx)); used.append(idx)
        if not pieces: raise ValueError(f'frame {fi} has no visible pieces')
        rec=bytearray()
        for v in (c0,c1,c2,ox,oy,cw,ch): rec += int(v).to_bytes(2,'big')
        rec += bytes([flags,len(pieces)])
        for x,y,w in pieces: rec += bytes([x,y])+w.to_bytes(2,'big')
        records.append(bytes(rec))
        manifests.append({'frame':fi,'piece_count':len(pieces),'chunk_indices':used,'unique_chunks_in_frame':len(set(used)),'record_bytes':len(rec)})
    return records,b''.join(chunks),{'frame_count':len(frames),'group':group,'global_unique_chunks':len(chunks),'chunk_bytes':128,'total_chunk_bytes':len(chunks)*128,'frames':manifests,'max_frame_working_set':max(x['unique_chunks_in_frame'] for x in manifests)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);ap.add_argument('out_prefix',type=Path);a=ap.parse_args()
    spec=json.loads(a.manifest.read_text()); base=a.manifest.parent; frames=[]
    for f in spec['frames']:
        img=indexed_image((base/f['image']).resolve(), (base/f['palette_json']).resolve() if f.get('palette_json') else None)
        row=dict(f);row['image']=img;frames.append(row)
    records,chunks,meta=compile_sequence(frames,group=int(spec.get('group',0)))
    p=a.out_prefix;p.parent.mkdir(parents=True,exist_ok=True);p.with_suffix('.chunks.bin').write_bytes(chunks)
    blob=bytearray();offs=[]
    for r in records:offs.append(len(blob));blob+=r
    p.with_suffix('.records.bin').write_bytes(blob);meta['record_offsets']=offs;p.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
