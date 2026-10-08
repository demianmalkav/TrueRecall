#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from vm_disasm import EXPECTED_SIZE,EXPECTED_SHA1
from vm_region_source_export import export_region_source
from vm_asm import assemble,parse_text

TEST_TYPES=(38,104,105,28)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args()
    rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
    rows=[]
    for tid in TEST_TYPES:
        meta,source=export_region_source(rom,tid)
        built,_labels=assemble(parse_text(source),meta['start'])
        expected=rom[meta['start']:meta['end']]
        assert built==expected,(tid,hex(meta['start']),hex(meta['end']),len(built),len(expected))
        rows.append({
            'type_id':tid,
            'start':f"0x{meta['start']:06X}",
            'end':f"0x{meta['end']:06X}",
            'bytes':meta['bytes'],
            'reachable_instruction_addresses':meta['reachable_instruction_addresses'],
            'external_reachable_instruction_addresses':meta['external_reachable_instruction_addresses'],
            'raw_blocks':meta['raw_blocks'],
            'raw_bytes':meta['raw_bytes'],
            'byte_identical':True,
        })
    report={
        'schema':'truerecall.vm_region_roundtrip.v1',
        'base_sha1':digest,
        'types':rows,
        'policy':'Raw blocks preserve bytes inside the owned reachable-code hull that are not proven instructions. They are opaque and make relocation unsafe until their semantics/embedded addresses are recovered.',
        'all_regions_byte_identical':True,
    }
    text=json.dumps(report,indent=2,sort_keys=True);print(text)
    if a.json:a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
