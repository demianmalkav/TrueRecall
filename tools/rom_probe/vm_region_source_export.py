#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib
from pathlib import Path
from vm_disasm import EXPECTED_SIZE,EXPECTED_SHA1,TYPE_SELECTOR_TABLE,TYPE_POINTER_TABLE,reachable,u32
from vm_source_export import source_ins

def next_script_start(rom:bytes,start:int)->int:
    starts=sorted(u32(rom,TYPE_POINTER_TABLE+i*4) for i in range(139) if rom[TYPE_SELECTOR_TABLE+i]==1)
    for value in starts:
        if value>start:return value
    return len(rom)

def export_region_source(rom:bytes,type_id:int):
    if rom[TYPE_SELECTOR_TABLE+type_id]==0:raise ValueError('direct-code type cannot be exported as VM source')
    start=u32(rom,TYPE_POINTER_TABLE+type_id*4)
    limit=next_script_start(rom,start)
    insns,labels,_states=reachable(rom,start,max_states=200000,max_stack=32)
    owned={pc:ins for pc,ins in insns.items() if start<=pc<limit}
    if not owned:raise ValueError('no owned reachable instructions')
    end=max(ins['end'] for ins in owned.values())
    internal=set(owned)
    lines=[f'; TrueRecall VM region source for type_id {type_id}',f'; original start 0x{start:06X}',f'; canonical base SHA1 {EXPECTED_SHA1}',f'; owned forward region limit 0x{limit:06X}; emitted hull end 0x{end:06X}','']
    pc=start; raw_bytes=0; raw_blocks=0
    for here,ins in sorted(owned.items()):
        if here<pc:continue
        if here>pc:
            raw=rom[pc:here]
            lines.append(f'  .raw {raw.hex().upper()}  ; unclassified bytes 0x{pc:06X}..0x{here:06X}')
            raw_bytes+=len(raw);raw_blocks+=1;pc=here
        if here in labels:lines.append(f'L_{here:06X}:')
        lines.append('  '+source_ins(ins,internal))
        pc=ins['end']
    if pc<end:
        raw=rom[pc:end];lines.append(f'  .raw {raw.hex().upper()}  ; unclassified bytes 0x{pc:06X}..0x{end:06X}')
        raw_bytes+=len(raw);raw_blocks+=1
    meta={'type_id':type_id,'start':start,'limit':limit,'end':end,'bytes':end-start,'reachable_instruction_addresses':len(owned),'raw_blocks':raw_blocks,'raw_bytes':raw_bytes,'external_reachable_instruction_addresses':len(insns)-len(owned)}
    return meta,'\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--type',required=True,type=lambda x:int(x,0));ap.add_argument('--out',type=Path);a=ap.parse_args()
    rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;assert hashlib.sha1(rom).hexdigest()==EXPECTED_SHA1
    meta,text=export_region_source(rom,a.type);print(text,end='')
    if a.out:a.out.write_text(text,encoding='utf-8')
    print(f'; region bytes={meta["bytes"]} raw_blocks={meta["raw_blocks"]} raw_bytes={meta["raw_bytes"]}')
if __name__=='__main__':main()
