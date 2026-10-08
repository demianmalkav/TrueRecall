#!/usr/bin/env python3
"""M0.6I regression: replace one scene-0 placement type, preserving layout exactly."""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
from object_stream_codec import parse_scene, serialize_preserving_layout
from lzbeam_codec import encode_stream, decode_stream

EXPECTED_SIZE=2_097_152; EXPECTED_SHA1="d39174bed46ede85531b86df7ba49123ce2f8411"
SCENE=0; PLACEMENT_INDEX=2; EXPECTED_TYPE=68; NEW_TYPE=54; EXPECTED_X=240; EXPECTED_Y=75
NEW_LZ=0x1FB000; FREE_START=0x1FABC3; FREE_END=0x200000; CHECKSUM_OFFSET=0x018E
EXPECTED_OUTPUT_SHA1="b1754bb986e3450456a30c17a54a3ccb4633783b"

def checksum(buf):
    total=0
    for off in range(0x200,len(buf),2): total=(total+((buf[off]<<8)|buf[off+1]))&0xFFFF
    return total

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("rom",type=Path); ap.add_argument("output",type=Path); a=ap.parse_args(); raw=a.rom.read_bytes()
    assert len(raw)==EXPECTED_SIZE and hashlib.sha1(raw).hexdigest()==EXPECTED_SHA1
    stream=parse_scene(raw,SCENE); original=decode_stream(raw,stream.source_lz); target=stream.placements[PLACEMENT_INDEX]
    assert (target.type_id,target.x,target.y,target.stride)==(EXPECTED_TYPE,EXPECTED_X,EXPECTED_Y,6)
    rows=list(stream.placements); rows[PLACEMENT_INDEX]=target.with_type(NEW_TYPE); edited=serialize_preserving_layout(stream,rows)
    diffs=[off for off in range(0,len(original),2) if original[off:off+2]!=edited[off:off+2]]; assert diffs==[target.decoded_offset]
    encoded=encode_stream(edited); assert decode_stream(encoded)==edited
    assert NEW_LZ>=FREE_START and NEW_LZ+len(encoded)<=FREE_END and all(x==0xFF for x in raw[NEW_LZ:NEW_LZ+len(encoded)])
    out=bytearray(raw); out[NEW_LZ:NEW_LZ+len(encoded)]=encoded; out[stream.descriptor+6:stream.descriptor+10]=NEW_LZ.to_bytes(4,"big"); out[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2]=checksum(out).to_bytes(2,"big")
    rebuilt=parse_scene(bytes(out),SCENE); assert rebuilt.source_lz==NEW_LZ and len(rebuilt.placements)==len(stream.placements)
    for i,(before,after) in enumerate(zip(stream.placements,rebuilt.placements)):
        if i==PLACEMENT_INDEX: assert after.type_id==NEW_TYPE and after.status_flags==before.status_flags and after.x==before.x and after.y==before.y and after.stride==before.stride
        else: assert (after.stride,after.status,after.x,after.y,after.param)==(before.stride,before.status,before.x,before.y,before.param)
    digest=hashlib.sha1(out).hexdigest(); assert digest==EXPECTED_OUTPUT_SHA1; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(out)
    print(f"M0.6I OK output_sha1={digest} checksum=0x{checksum(out):04X}")
if __name__=="__main__": main()
