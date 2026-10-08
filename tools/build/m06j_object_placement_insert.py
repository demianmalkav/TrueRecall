#!/usr/bin/env python3
"""M0.6J regression: append one stride-6 health pickup to scene 1."""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
from object_stream_codec import parse_scene
from lzbeam_codec import encode_stream, decode_stream

EXPECTED_SIZE=2_097_152; EXPECTED_SHA1="d39174bed46ede85531b86df7ba49123ce2f8411"
SCENE=1; NEW_TYPE=54; NEW_X=256; NEW_Y=7984; NEW_STATUS_FLAGS=0x7800
NEW_LZ=0x1FB000; FREE_START=0x1FABC3; FREE_END=0x200000; CHECKSUM_OFFSET=0x018E
EXPECTED_OUTPUT_SHA1="de11dbcec3517d754fcadb253e45348b6362a318"

def checksum(buf):
    total=0
    for off in range(0x200,len(buf),2): total=(total+((buf[off]<<8)|buf[off+1]))&0xFFFF
    return total

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("rom",type=Path); ap.add_argument("output",type=Path); a=ap.parse_args(); raw=a.rom.read_bytes()
    assert len(raw)==EXPECTED_SIZE and hashlib.sha1(raw).hexdigest()==EXPECTED_SHA1
    stream=parse_scene(raw,SCENE); assert stream.stride_runs==[(6,72)] and stream.placement_count==72 and stream.start_offset==0x10 and stream.end_offset==0x1C0
    decoded=bytearray(decode_stream(raw,stream.source_lz)); decoded += (NEW_STATUS_FLAGS|NEW_TYPE).to_bytes(2,"big")+NEW_X.to_bytes(2,"big")+NEW_Y.to_bytes(2,"big")
    encoded=encode_stream(bytes(decoded)); assert decode_stream(encoded)==bytes(decoded)
    assert NEW_LZ>=FREE_START and NEW_LZ+len(encoded)<=FREE_END and all(x==0xFF for x in raw[NEW_LZ:NEW_LZ+len(encoded)])
    out=bytearray(raw); out[NEW_LZ:NEW_LZ+len(encoded)]=encoded; out[stream.descriptor:stream.descriptor+2]=(73).to_bytes(2,"big"); out[stream.descriptor+4:stream.descriptor+6]=(stream.end_offset+6).to_bytes(2,"big"); out[stream.descriptor+6:stream.descriptor+10]=NEW_LZ.to_bytes(4,"big"); out[stream.descriptor+0x0B]=73; out[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2]=checksum(out).to_bytes(2,"big")
    rebuilt=parse_scene(bytes(out),SCENE); assert rebuilt.placement_count==73 and rebuilt.stride_runs==[(6,73)] and rebuilt.end_offset==0x1C6
    p=rebuilt.placements[-1]; assert (p.type_id,p.status_flags,p.x,p.y,p.stride,p.param)==(54,0x7800,256,7984,6,None)
    digest=hashlib.sha1(out).hexdigest(); assert digest==EXPECTED_OUTPUT_SHA1; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(out)
    print(f"M0.6J OK output_sha1={digest} checksum=0x{checksum(out):04X}")
if __name__=="__main__": main()
