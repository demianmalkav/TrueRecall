#!/usr/bin/env python3
"""M0.6H: edit exactly one gameplay tilemap word and rebuild the LZ resource.

The experiment targets scene 0, C000 plane, tile (0,0), changing retail word
0x0000 to 0x020C. The edited decompressed map is encoded with TrueRecall LZBeam,
relocated into verified FF padding, and the retail map descriptor is redirected.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "lzbeam"))
from lzbeam_codec import decode_stream, encode_stream

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
SCENE_TABLE=0x013B4A
NEW_LZ=0x1FB000
FREE_START=0x1FABC3
FREE_END=0x200000
CHECKSUM_OFFSET=0x018E
EDIT_X=0
EDIT_Y=0
EXPECTED_OLD=0x0000
NEW_WORD=0x020C

def u16(b,o):return int.from_bytes(b[o:o+2],'big')
def u32(b,o):return int.from_bytes(b[o:o+4],'big')
def checksum(b):
    total=0
    for off in range(0x200,len(b),2):total=(total+((b[off]<<8)|b[off+1]))&0xffff
    return total

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();raw=a.rom.read_bytes()
    assert len(raw)==EXPECTED_SIZE;digest=hashlib.sha1(raw).hexdigest();assert digest==EXPECTED_SHA1
    record=u32(raw,SCENE_TABLE);map_desc=u32(raw,record+0x1A);retail_lz=u32(raw,map_desc);width=u16(raw,map_desc+4);height=u16(raw,map_desc+6)
    original=decode_stream(raw,retail_lz);assert len(original)==width*height*2
    offset=(EDIT_Y*width+EDIT_X)*2;assert u16(original,offset)==EXPECTED_OLD
    edited=bytearray(original);edited[offset:offset+2]=NEW_WORD.to_bytes(2,'big');encoded=encode_stream(bytes(edited));assert decode_stream(encoded)==bytes(edited)
    assert NEW_LZ>=FREE_START and NEW_LZ+len(encoded)<=FREE_END and all(x==0xff for x in raw[NEW_LZ:NEW_LZ+len(encoded)])
    out=bytearray(raw);out[NEW_LZ:NEW_LZ+len(encoded)]=encoded;out[map_desc:map_desc+4]=NEW_LZ.to_bytes(4,'big');out[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2]=checksum(out).to_bytes(2,'big')
    rebuilt=decode_stream(bytes(out),NEW_LZ);diff=[i for i in range(0,len(original),2) if original[i:i+2]!=rebuilt[i:i+2]]
    assert diff==[offset];assert u16(rebuilt,offset)==NEW_WORD
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(out)
    print(f'base_sha1={digest}');print(f'dimensions={width}x{height} edit=({EDIT_X},{EDIT_Y}) 0x{EXPECTED_OLD:04X}->0x{NEW_WORD:04X}');print(f'encoded_bytes={len(encoded)} differing_map_words={len(diff)}');print(f'checksum=0x{checksum(out):04X}');print(f'output_sha1={hashlib.sha1(out).hexdigest()}')
if __name__=='__main__':main()
