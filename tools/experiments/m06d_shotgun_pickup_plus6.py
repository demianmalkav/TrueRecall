#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import sys

# Allow running directly from repository root or tools/experiments.
ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/'tools'/'rom_probe'
if str(PROBE) not in sys.path: sys.path.insert(0,str(PROBE))

from vm_source_export import export_type_source
from vm_asm import assemble,parse_text

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TYPE_ID=69
OLD_SOURCE='MOVI_W_D1 0x0005'
NEW_SOURCE='MOVI_W_D1 0x0006'
EXPECTED_SCRIPT_DIFF_OFFSET=0x1762C1
EXPECTED_RESULT_SHA1='ff1f6fa5fe3815c6e3bf093ffd5e5431f2251469'

def checksum(buf:bytes|bytearray)->int:
    total=0
    for i in range(0x200,len(buf),2):
        word=(buf[i]<<8)|(buf[i+1] if i+1<len(buf) else 0)
        total=(total+word)&0xFFFF
    return total

def main():
    ap=argparse.ArgumentParser(description='M0.6D controlled VM experiment: shotgun weapon pickup grants 6 shells instead of 5.')
    ap.add_argument('base_rom',type=Path)
    ap.add_argument('output_rom',type=Path)
    ap.add_argument('--manifest',type=Path)
    a=ap.parse_args()

    base=a.base_rom.read_bytes()
    if len(base)!=EXPECTED_SIZE: raise SystemExit(f'wrong ROM size: {len(base)}')
    digest=hashlib.sha1(base).hexdigest()
    if digest!=EXPECTED_SHA1: raise SystemExit(f'wrong base ROM SHA-1: {digest}')
    header_ck=int.from_bytes(base[0x18E:0x190],'big')
    computed=checksum(base)
    if header_ck!=computed: raise SystemExit(f'base checksum mismatch: header={header_ck:04X} computed={computed:04X}')

    start,source=export_type_source(base,TYPE_ID)
    if source.count(OLD_SOURCE)!=1: raise SystemExit('expected exactly one +5-shell source immediate')
    modified_source=source.replace(OLD_SOURCE,NEW_SOURCE)
    old_script,_=assemble(parse_text(source),start)
    new_script,_=assemble(parse_text(modified_source),start)
    if old_script!=base[start:start+len(old_script)]: raise SystemExit('source exporter/assembler does not reproduce retail type69')
    if len(old_script)!=len(new_script): raise SystemExit('experiment unexpectedly changed script size')
    script_diffs=[(start+i,x,y) for i,(x,y) in enumerate(zip(old_script,new_script)) if x!=y]
    if script_diffs!=[(EXPECTED_SCRIPT_DIFF_OFFSET,0x05,0x06)]: raise SystemExit(f'unexpected script diff: {script_diffs}')

    out=bytearray(base)
    out[start:start+len(new_script)]=new_script
    new_checksum=checksum(out)
    out[0x18E:0x190]=new_checksum.to_bytes(2,'big')
    result_sha1=hashlib.sha1(out).hexdigest()
    if result_sha1!=EXPECTED_RESULT_SHA1: raise SystemExit(f'unexpected result SHA-1: {result_sha1}')

    all_diffs=[{'offset':f'0x{i:06X}','old':f'0x{base[i]:02X}','new':f'0x{out[i]:02X}'} for i in range(len(base)) if base[i]!=out[i]]
    expected_offsets={'0x00018F','0x1762C1'}
    if {row['offset'] for row in all_diffs}!=expected_offsets: raise SystemExit(f'unexpected ROM diff set: {all_diffs}')

    a.output_rom.write_bytes(out)
    report={
        'schema':'truerecall.experiment.m06d_shotgun_pickup_plus6.v1',
        'base_sha1':EXPECTED_SHA1,
        'result_sha1':result_sha1,
        'base_header_checksum':f'0x{header_ck:04X}',
        'result_header_checksum':f'0x{new_checksum:04X}',
        'type_id':TYPE_ID,
        'script_base':f'0x{start:06X}',
        'behavior_change':'shotgun weapon pickup grants 6 shells instead of 5',
        'gameplay_byte_change':{'offset':f'0x{EXPECTED_SCRIPT_DIFF_OFFSET:06X}','old':'0x05','new':'0x06'},
        'all_rom_byte_diffs':all_diffs,
        'runtime_validation':'NOT_PERFORMED — no Genesis emulator/debugger is available in the current execution environment',
    }
    text=json.dumps(report,indent=2,sort_keys=True)
    print(text)
    if a.manifest:a.manifest.write_text(text+'\n',encoding='utf-8')

if __name__=='__main__':main()
