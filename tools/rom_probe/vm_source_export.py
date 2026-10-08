#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib
from pathlib import Path
from vm_disasm import EXPECTED_SIZE,EXPECTED_SHA1,TYPE_SELECTOR_TABLE,TYPE_POINTER_TABLE,NATIVES,MN,OPERAND_BYTES,reachable,u32

def source_ins(ins,internal):
    op=ins['op']; o=ins.get('operand')
    label=lambda t: f'L_{t:06X}' if t in internal else f'0x{t:06X}'
    if op==0x0000:return f'BR_TRUE {label(ins["target"])}'
    if op==0x0004:return f'BR_FALSE {label(ins["target"])}'
    if op==0x0008:return f'JMP {label(ins["target"])}'
    if op==0x000C:return f'CALL {label(ins["target"])}'
    if op==0x0010:return 'RET_OR_END'
    if op==0x00AC:return 'SWITCH_D2 ' + ', '.join(f'0x{v:04X}:{label(t)}' for v,t in ins['cases'])
    if op==0x00E4:return 'NATIVE ' + NATIVES.get(o,f'0x{o:06X}')
    name=MN.get(op,f'OP_{op:04X}')
    if o is None:return name
    width=OPERAND_BYTES[op]
    return f'{name} 0x{o:0{width*2}X}'

def export_type_source(rom:bytes,type_id:int):
    if rom[TYPE_SELECTOR_TABLE+type_id]==0:raise ValueError('direct-code type cannot be exported as VM source')
    start=u32(rom,TYPE_POINTER_TABLE+type_id*4);insns,labels,_=reachable(rom,start,max_states=200000,max_stack=32)
    rows=sorted((pc,ins) for pc,ins in insns.items())
    for (pc,ins),(npc,_nins) in zip(rows,rows[1:]):
        if ins['end']!=npc:raise ValueError(f'non-contiguous reachable script: gap 0x{ins["end"]:06X}..0x{npc:06X}')
    internal=set(insns)
    lines=[f'; TrueRecall object VM source for type_id {type_id}',f'; original start 0x{start:06X}',f'; canonical base SHA1 {EXPECTED_SHA1}','']
    for pc,ins in rows:
        if pc in labels:lines.append(f'L_{pc:06X}:')
        lines.append('  '+source_ins(ins,internal))
    return start,'\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--type',required=True,type=lambda x:int(x,0));ap.add_argument('--out',type=Path);a=ap.parse_args()
    rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;assert hashlib.sha1(rom).hexdigest()==EXPECTED_SHA1
    _start,text=export_type_source(rom,a.type);print(text,end='')
    if a.out:a.out.write_text(text,encoding='utf-8')
if __name__=='__main__':main()
