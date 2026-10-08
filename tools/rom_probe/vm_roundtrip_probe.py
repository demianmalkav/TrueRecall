#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from vm_disasm import EXPECTED_SIZE,EXPECTED_SHA1,TYPE_SELECTOR_TABLE,TYPE_POINTER_TABLE,OPERAND_BYTES,decode,reachable,u16,u32

def w(v): return int(v&0xFFFF).to_bytes(2,'big')
def l(v): return int(v&0xFFFFFFFF).to_bytes(4,'big')

def encode(ins:dict)->bytes:
    op=ins['op']; out=bytearray(w(op))
    if op in (0x0000,0x0004,0x0008):
        out += w(ins['target'])
    elif op==0x000C:
        out += l(ins['target'])
    elif op==0x0010:
        pass
    elif op==0x00AC:
        out += w(len(ins['cases']))
        for value,target in ins['cases']:
            out += w(value); out += w(target)
    else:
        size=OPERAND_BYTES[op]
        if size:
            out += int(ins['operand']).to_bytes(size,'big')
    return bytes(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args()
    rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
    scripted=[i for i in range(139) if rom[TYPE_SELECTOR_TABLE+i]==1]
    assert len(scripted)==136
    total_ins=0; unique={}; per_type={}; opcode_counts=Counter()
    for tid in scripted:
        start=u32(rom,TYPE_POINTER_TABLE+tid*4)
        insns,labels,states=reachable(rom,start,max_states=200000,max_stack=32)
        assert insns,(tid,hex(start))
        for pc,ins in insns.items():
            assert not ins.get('bad'),(tid,hex(pc),hex(ins['op']))
            enc=encode(ins); raw=rom[pc:pc+len(enc)]
            assert enc==raw,(tid,hex(pc),enc.hex(),raw.hex(),ins)
            opcode_counts[ins['op']]+=1
            unique[pc]=ins
        total_ins += len(insns)
        per_type[tid]={'reachable_instructions':len(insns),'traversal_states':states,'start':f'0x{start:06X}'}
    all_ops=set(opcode_counts)
    expected=set(range(0,0x120,4))
    assert all_ops <= expected
    unused=sorted(expected-all_ops)
    report={
      'schema':'truerecall.vm_roundtrip.v1','base_sha1':digest,
      'scripted_type_ids':len(scripted),'total_per_type_reachable_instruction_visits':total_ins,
      'unique_reachable_instruction_addresses':len(unique),'opcodes_covered_by_retail':len(all_ops),
      'vm_opcode_capacity':72,'unused_opcode_offsets_in_retail':[f'0x{x:04X}' for x in unused],
      'all_reencoded_bytes_match':True,
      'opcode_counts':{f'0x{k:04X}':v for k,v in sorted(opcode_counts.items())},
      'notes':{
        'branch_encoding':'conditional/unconditional local branches store low 16 bits of bank-local target',
        'call_encoding':'VM CALL stores an absolute 32-bit target',
        'switch_encoding':'count followed by word value + bank-local low-word target pairs',
        'scope':'reachable instructions from retail scripted type IDs 0..138; shared VM subroutines may be visited from multiple roots'
      }
    }
    text=json.dumps(report,indent=2,sort_keys=True);print(text)
    if a.json:a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
