#!/usr/bin/env python3
"""Validate TrueRecall's LZBeam encoder against all scene/cutscene resources.

The probe derives resource pointers from retail tables, decodes each block,
re-encodes the decompressed bytes and requires decode(new)==decode(retail).
It also compares the new stream length with the number of retail bytes actually
consumed by the decoder.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lzbeam'))
from lzbeam_codec import decode_stream, encode_stream

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
SCENE_TABLE=0x013B4A
CUTSCENE_TABLE=0x00AC3A

def u16(b,o):return int.from_bytes(b[o:o+2],'big')
def u32(b,o):return int.from_bytes(b[o:o+4],'big')

def retail_consumed(rom:bytes,off:int):
    out_len=u16(rom,off);command_offset=u16(rom,off+2);read_pos=off+4;command_start=off+command_offset+2;command_pos=command_start;bits_left=0;current=0;out=bytearray()
    def bit():
        nonlocal command_pos,bits_left,current
        if bits_left==0:current=rom[command_pos];command_pos+=1;bits_left=8
        value=(current>>7)&1;current=(current<<1)&255;bits_left-=1;return value
    def bits(count):
        value=0
        for _ in range(count):value=(value<<1)|bit()
        return value
    def count():
        value=1
        while bit()==0:value=(value<<1)|bit()
        return value
    n=count();out.extend(rom[read_pos:read_pos+n]);read_pos+=n
    while len(out)<out_len:
        written=len(out);width=written.bit_length() if written<256 else 8+(written>>8).bit_length();source=bits(width);n=count()+2
        if source>=len(out):raise ValueError((hex(off),source,len(out)))
        for i in range(n):
            out.append(out[source+i])
            if len(out)>=out_len:break
        if len(out)<out_len and bit()==0:
            n=count();out.extend(rom[read_pos:read_pos+n]);read_pos+=n
    return bytes(out[:out_len]),max(read_pos,command_pos)-off

def resources(rom:bytes):
    refs={}
    def add(ptr,label):refs.setdefault(ptr,[]).append(label)
    for scene in range(19):
        record=u32(rom,SCENE_TABLE+scene*4)
        object_desc=u32(rom,record+0x0A);add(u32(rom,object_desc+6),f'scene{scene}.objects')
        for block,name in ((0x16,'c000'),(0x22,'e000')):
            gfx_desc=u32(rom,record+block);map_desc=u32(rom,record+block+4)
            if gfx_desc:add(u32(rom,gfx_desc),f'scene{scene}.{name}.gfx')
            add(u32(rom,map_desc),f'scene{scene}.{name}.map')
    pos=CUTSCENE_TABLE
    for group in range(32):
        count=u16(rom,pos)
        if count==0 or count>8:break
        pos+=2
        for frame in range(count):
            add(u32(rom,pos),f'cut{group}.{frame}.gfx');add(u32(rom,pos+4),f'cut{group}.{frame}.map');pos+=16
    return refs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rom=a.rom.read_bytes()
    assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
    refs=resources(rom);rows=[]
    for off in sorted(refs):
        decoded,retail_bytes=retail_consumed(rom,off);encoded=encode_stream(decoded);assert decode_stream(encoded)==decoded
        rows.append({'offset':f'0x{off:06X}','decoded_bytes':len(decoded),'retail_compressed_bytes':retail_bytes,'new_compressed_bytes':len(encoded),'new_over_retail':len(encoded)/retail_bytes,'fits_retail_footprint':len(encoded)<=retail_bytes,'references':refs[off]})
    assert len(rows)==102
    fits=sum(row['fits_retail_footprint'] for row in rows);ratio=sum(row['new_over_retail'] for row in rows)/len(rows)
    assert fits==78
    report={'schema':'truerecall.lzbeam_encode_roundtrip.v1','base_sha1':digest,'resource_count':len(rows),'decode_encode_decode_identical':True,'fits_existing_retail_footprint_count':fits,'larger_than_retail_count':len(rows)-fits,'mean_new_over_retail':ratio,'rows':rows,'policy':'Functional round-trip means decompressed bytes are identical. The new compressed bitstream is deterministic but is not required to match Beam original bytes.'}
    text=json.dumps(report,indent=2,sort_keys=True);print(text)
    if a.json:a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
