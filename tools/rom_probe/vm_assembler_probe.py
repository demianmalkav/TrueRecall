#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from vm_disasm import EXPECTED_SIZE,EXPECTED_SHA1,TYPE_POINTER_TABLE,reachable,u32
from vm_source_export import export_type_source
from vm_asm import assemble,parse_text

CONTIGUOUS_TYPES=(51,54,61,69,70,5,12,46)
RELOCATE_TYPE=69
RELOCATE_BASE=0x177000


def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args()
    rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
    rows=[]
    for tid in CONTIGUOUS_TYPES:
        start,source=export_type_source(rom,tid)
        built,labels=assemble(parse_text(source),start)
        assert built==rom[start:start+len(built)],(tid,hex(start),len(built))
        insns,_labels,_states=reachable(rom,start,max_states=200000,max_stack=32)
        end=max(i['end'] for i in insns.values())
        assert len(built)==end-start,(tid,hex(start),len(built),hex(end-start))
        rows.append({'type_id':tid,'base':f'0x{start:06X}','bytes':len(built),'instruction_addresses':len(insns),'byte_identical':True})

    original_start,source=export_type_source(rom,RELOCATE_TYPE)
    original,labels0=assemble(parse_text(source),original_start)
    relocated,labels1=assemble(parse_text(source),RELOCATE_BASE)
    assert len(original)==len(relocated)
    assert labels0.keys()==labels1.keys()
    delta=RELOCATE_BASE-original_start
    for name in labels0:
        assert labels1[name]==labels0[name]+delta,(name,hex(labels0[name]),hex(labels1[name]),hex(delta))

    # Validate relocated control-flow shape by decoding from the synthetic buffer at its logical base.
    # Pad a bytearray so the existing ROM-indexed decoder can inspect the relocated bytes directly.
    synthetic=bytearray(max(RELOCATE_BASE+len(relocated)+16,len(rom)))
    synthetic[:len(rom)]=rom
    synthetic[RELOCATE_BASE:RELOCATE_BASE+len(relocated)]=relocated
    ins0,_l0,_s0=reachable(rom,original_start,max_states=200000,max_stack=32)
    ins1,_l1,_s1=reachable(bytes(synthetic),RELOCATE_BASE,max_states=200000,max_stack=32)
    assert len(ins0)==len(ins1)==68
    norm0=sorted((pc-original_start,ins['op'],ins.get('end',pc)-pc) for pc,ins in ins0.items())
    norm1=sorted((pc-RELOCATE_BASE,ins['op'],ins.get('end',pc)-pc) for pc,ins in ins1.items())
    assert norm0==norm1
    report={
      'schema':'truerecall.vm_assembler_probe.v1','base_sha1':digest,
      'original_roundtrip_types':rows,
      'relocation':{
        'type_id':RELOCATE_TYPE,'original_base':f'0x{original_start:06X}','relocated_base':f'0x{RELOCATE_BASE:06X}',
        'bytes':len(relocated),'instruction_addresses':len(ins1),'label_count':len(labels1),
        'all_symbolic_labels_relocated_by_delta':True,'normalized_instruction_shape_matches':True
      },
      'policy':'Only contiguous reachable retail scripts are accepted by the source exporter; scripts containing gaps/embedded data remain rejected until explicit directives exist.'
    }
    text=json.dumps(report,indent=2,sort_keys=True);print(text)
    if a.json:a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
