#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import defaultdict, deque
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from initial_visual_cfg_probe import decode
from level_objects_probe import u32

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TS=0x07A33C; TP=0x07953E
F7CC=bytes.fromhex('4eb90000f7cc')
ABS_JMP=bytes.fromhex('4ef9')
RTS=bytes.fromhex('4e75')

def native_roots(rom:bytes):
    roots=defaultdict(set)
    for tid in range(139):
        if rom[TS+tid]!=1: continue
        start=u32(rom,TP+tid*4); q=deque([(start,())]); seen=set()
        while q and len(seen)<50000:
            pc,stack=q.popleft(); key=(pc,stack)
            if key in seen or not(0<=pc<len(rom)-2): continue
            seen.add(key); ins=decode(rom,pc)
            if ins.get('bad'): continue
            op=ins['op']
            if op==0xE4: roots[ins.get('operand')].add(tid)
            if op in (0,4): q.append((ins['target'],stack)); q.append((ins['end'],stack))
            elif op==8: q.append((ins['target'],stack))
            elif op==0xC:
                if len(stack)<16:q.append((ins['target'],stack+(ins['end'],)))
            elif op==0x10:
                if stack:q.append((stack[-1],stack[:-1]))
            elif op==0xAC:
                for _,t in ins['cases']:q.append((t,stack))
                q.append((ins['end'],stack))
            else:q.append((ins['end'],stack))
    return roots

def even_find(rom:bytes, sig:bytes, start:int, end:int):
    p=start
    while True:
        p=rom.find(sig,p,end)
        if p<0:return -1
        if (p-start)%2==0:return p
        p+=1

def linear_tail(rom:bytes,start:int,limit:int=0x1000):
    end=min(start+limit,len(rom))
    j=even_find(rom,ABS_JMP,start,end); r=even_find(rom,RTS,start,end)
    candidates=[]
    if j>=0:candidates.append((j,j+6,'JMP',u32(rom,j+2)))
    if r>=0:candidates.append((r,r+2,'RTS',None))
    return min(candidates,key=lambda x:x[0]) if candidates else None

def fixed_spawns(rom:bytes,start:int,body_end:int):
    rows=[];p=start
    while True:
        p=rom.find(F7CC,p,body_end)
        if p<0:break
        if (p-start)%2:
            p+=1;continue
        typ=None
        for back in range(4,18,2):
            q=p-back
            if q>=start and rom[q:q+2]==bytes.fromhex('303c'):
                typ=int.from_bytes(rom[q+2:q+4],'big');break
        rows.append({'call':p,'type_id':typ});p+=2
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args()
    rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
    roots=native_roots(rom); rows=[]
    for target,tids in sorted(roots.items()):
        tail=linear_tail(rom,target)
        if not tail:continue
        at,end,kind,dst=tail; spawns=fixed_spawns(rom,target,end)
        if spawns or target in (0x20D8,0xDA72,0xDAA4,0xDB48):
            rows.append({'native':f'0x{target:06X}','root_type_ids':sorted(tids),'linear_terminal':{'address':f'0x{at:06X}','kind':kind,'target':None if dst is None else f'0x{dst:06X}'},'allocator_calls':[{'address':f'0x{x["call"]:06X}','fixed_type_id':x['type_id']} for x in spawns]})
    by={int(r['native'],16):r for r in rows}
    assert by[0x20D8]['allocator_calls']==[{'address':'0x0020DE','fixed_type_id':None}]
    assert by[0xDA72]['linear_terminal']['target']=='0x010224' and by[0xDA72]['allocator_calls']==[]
    assert [x['fixed_type_id'] for x in by[0xDAA4]['allocator_calls']]==[175,175]
    assert [x['fixed_type_id'] for x in by[0xDB48]['allocator_calls']]==[170]
    report={'schema':'truerecall.native_spawn.v1','base_sha1':digest,'native_targets_scanned':len(roots),'rows':rows,'confirmed':{'generic_linked_spawn_native':'0x0020D8','spread_projectile_native':'0x00DAA4','spread_projectile_type':175,'standard_projectile_native':'0x00DB48','standard_projectile_type':170},'method_note':'Native wrappers are bounded conservatively at the first even-aligned absolute JMP tail or RTS on the linear entry path. This prevents fixed-window bleed; it is not a full 68000 CFG and therefore reports only fixed allocator calls proven before that terminal.'}
    text=json.dumps(report,indent=2,sort_keys=True);print(text)
    if a.json:a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
