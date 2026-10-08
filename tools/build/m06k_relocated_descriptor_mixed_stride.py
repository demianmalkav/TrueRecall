#!/usr/bin/env python3
"""M0.6K regression: add a stride-8 placement and relocate descriptor+stream."""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
from object_stream_codec import parse_scene, Placement, serialize_compiled, build_descriptor
from lzbeam_codec import encode_stream, decode_stream

EXPECTED_SIZE=2_097_152; EXPECTED_SHA1="d39174bed46ede85531b86df7ba49123ce2f8411"
SCENE=1; NEW_TYPE=123; NEW_X=256; NEW_Y=8000; NEW_PARAM=0; FLAGS=0x7800
NEW_DESC=0x1FABC4; NEW_LZ=0x1FB000; FREE_START=0x1FABC3; FREE_END=0x200000; CHECKSUM_OFFSET=0x018E
EXPECTED_OUTPUT_SHA1="db2031b93c987cb77ca5b3dc67e9d4e0cbe81327"

def checksum(buf):
    total=0
    for off in range(0x200,len(buf),2): total=(total+((buf[off]<<8)|buf[off+1]))&0xFFFF
    return total

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("rom",type=Path); ap.add_argument("output",type=Path); a=ap.parse_args(); raw=a.rom.read_bytes()
    assert len(raw)==EXPECTED_SIZE and hashlib.sha1(raw).hexdigest()==EXPECTED_SHA1
    stream=parse_scene(raw,SCENE); assert stream.stride_runs==[(6,72)] and stream.placement_count==72
    new=Placement(index=72,stride=8,status=FLAGS|NEW_TYPE,x=NEW_X,y=NEW_Y,param=NEW_PARAM,decoded_offset=-1)
    decoded,runs=serialize_compiled(stream.prefix,list(stream.placements)+[new]); assert runs==[(6,72),(8,1)] and len(decoded)==0x1C8
    encoded=encode_stream(decoded); assert decode_stream(encoded)==decoded
    descriptor=build_descriptor(count=73,start=len(stream.prefix),end=len(decoded),source_lz=NEW_LZ,runs=runs); assert len(descriptor)==14
    assert NEW_DESC>=FREE_START and NEW_DESC+len(descriptor)<=NEW_LZ and all(x==0xFF for x in raw[NEW_DESC:NEW_DESC+len(descriptor)]) and all(x==0xFF for x in raw[NEW_LZ:NEW_LZ+len(encoded)])
    out=bytearray(raw); out[NEW_DESC:NEW_DESC+len(descriptor)]=descriptor; out[NEW_LZ:NEW_LZ+len(encoded)]=encoded; out[stream.scene_ptr+0x0A:stream.scene_ptr+0x0E]=NEW_DESC.to_bytes(4,"big"); out[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2]=checksum(out).to_bytes(2,"big")
    rebuilt=parse_scene(bytes(out),SCENE); assert rebuilt.descriptor==NEW_DESC and rebuilt.source_lz==NEW_LZ and rebuilt.stride_runs==runs and rebuilt.placement_count==73
    p=rebuilt.placements[-1]; assert (p.stride,p.type_id,p.status_flags,p.x,p.y,p.param)==(8,NEW_TYPE,FLAGS,NEW_X,NEW_Y,NEW_PARAM)
    digest=hashlib.sha1(out).hexdigest(); assert digest==EXPECTED_OUTPUT_SHA1; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(out)
    print(f"M0.6K OK output_sha1={digest} checksum=0x{checksum(out):04X}")
if __name__=="__main__": main()
