#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, deque
from pathlib import Path
from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TYPE_SELECTOR_TABLE=0x07A33C
TYPE_POINTER_TABLE=0x07953E
ARCHETYPE_TABLE=0x079906
VM_ANIMATION_NATIVE=0x001F9A
OPERAND_BYTES={
0x0014:2,0x0018:2,0x001C:2,0x0020:4,0x0024:4,0x0028:4,0x002C:2,0x0030:4,
0x0034:2,0x0038:2,0x003C:2,0x0040:2,0x0044:0,0x0048:0,0x004C:0,0x0050:0,
0x0054:4,0x0058:4,0x005C:2,0x0060:4,0x0064:2,0x0068:2,0x006C:2,
0x0070:0,0x0074:0,0x0078:0,0x007C:0,0x0080:2,0x0084:4,0x0088:0,0x008C:0,
0x0090:0,0x0094:0,0x0098:0,0x009C:0,0x00A0:0,0x00A4:0,0x00A8:0,
0x00B0:0,0x00B4:0,0x00B8:0,0x00BC:0,0x00C0:0,0x00C4:0,0x00C8:0,0x00CC:0,
0x00D0:0,0x00D4:0,0x00D8:0,0x00DC:0,0x00E0:0,0x00E4:4,0x00E8:0,0x00EC:2,
0x00F0:0,0x00F4:0,0x00F8:0,0x00FC:0,0x0100:0,0x0104:0,0x0108:0,0x010C:0,
0x0110:0,0x0114:0,0x0118:0,0x011C:0,
}

def bank_target(pc:int, low:int)->int:
    return (pc & 0xFFFF0000) | low

def decode(rom:bytes, pc:int):
    op=u16(rom,pc); p=pc+2
    if op in (0x0000,0x0004,0x0008):
        low=u16(rom,p); p+=2
        return {'pc':pc,'op':op,'end':p,'target':bank_target(p,low)}
    if op==0x000C:
        target=u32(rom,p); p+=4
        return {'pc':pc,'op':op,'end':p,'target':target}
    if op==0x0010:
        return {'pc':pc,'op':op,'end':p}
    if op==0x00AC:
        count=u16(rom,p); p+=2; cases=[]
        for _ in range(count):
            value=u16(rom,p); target=bank_target(p+4,u16(rom,p+2)); p+=4
            cases.append((value,target))
        return {'pc':pc,'op':op,'end':p,'cases':cases}
    size=OPERAND_BYTES.get(op)
    if size is None: return {'pc':pc,'op':op,'bad':True}
    raw=rom[p:p+size]; p+=size
    return {'pc':pc,'op':op,'end':p,'operand':int.from_bytes(raw,'big') if size else None}

def canonical_selector(rom:bytes, e4pc:int):
    start=e4pc-12
    if start < 0: return None
    if u16(rom,start)!=0x001C: return None
    selector=u16(rom,start+2)
    if u16(rom,start+4)!=0x00F0: return None
    if u16(rom,start+6)!=0x001C: return None
    param=u16(rom,start+8)
    if u16(rom,start+10)!=0x00F0: return None
    return selector,param

def first_animation_calls(rom:bytes,type_id:int,max_states=200000,max_stack=16):
    if rom[TYPE_SELECTOR_TABLE+type_id]==0:
        return {'direct_code':True,'calls':[],'states':0,'truncated':False,'bad':None}
    start=u32(rom,TYPE_POINTER_TABLE+type_id*4)
    q=deque([(start,())]); seen=set(); calls=[]; bad=None; truncated=False
    while q:
        if len(seen)>=max_states:
            truncated=True; break
        pc,stack=q.popleft(); key=(pc,stack)
        if key in seen: continue
        seen.add(key)
        if not (0 <= pc < len(rom)-2): bad=f'pc_0x{pc:X}'; continue
        ins=decode(rom,pc)
        if ins.get('bad'):
            bad=f'bad_0x{ins["op"]:04X}@0x{pc:06X}'; continue
        op=ins['op']
        if op==0x00E4 and ins.get('operand')==VM_ANIMATION_NATIVE:
            cs=canonical_selector(rom,pc)
            calls.append({'pc':pc,'selector':None if cs is None else cs[0],'param':None if cs is None else cs[1],'canonical':cs is not None})
            continue
        if op in (0x0000,0x0004):
            q.append((ins['target'],stack)); q.append((ins['end'],stack))
        elif op==0x0008:
            q.append((ins['target'],stack))
        elif op==0x000C:
            if len(stack)<max_stack: q.append((ins['target'],stack+(ins['end'],)))
            else: truncated=True
        elif op==0x0010:
            if stack: q.append((stack[-1],stack[:-1]))
        elif op==0x00AC:
            for _,t in ins['cases']: q.append((t,stack))
            q.append((ins['end'],stack))
        else:
            q.append((ins['end'],stack))
    uniq=[]; seen_calls=set()
    for c in calls:
        k=(c['pc'],c['selector'],c['param'])
        if k not in seen_calls: seen_calls.add(k); uniq.append(c)
    return {'direct_code':False,'calls':uniq,'states':len(seen),'truncated':truncated,'bad':bad}

def placed_counts(rom:bytes):
    counts=Counter()
    for scene_index in range(SCENE_COUNT):
        scene=u32(rom,SCENE_TABLE+scene_index*4); desc=u32(rom,scene+0x0A)
        count=u16(rom,desc); start=u16(rom,desc+2); source=u32(rom,desc+6); decoded=lzbeam_decode(rom,source)
        p=desc+0x0A; total=0; runs=[]
        while total<count:
            stride=rom[p]; qty=rom[p+1]; p+=2; assert stride in (6,8) and qty>0; runs.append((stride,qty)); total+=qty
        pos=start
        for stride,qty in runs:
            for _ in range(qty): counts[u16(decoded,pos)&0x03FF]+=1; pos+=stride
    return counts

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('rom',type=Path); ap.add_argument('--json',type=Path); args=ap.parse_args()
    rom=args.rom.read_bytes(); assert len(rom)==EXPECTED_SIZE; digest=hashlib.sha1(rom).hexdigest(); assert digest==EXPECTED_SHA1
    counts=placed_counts(rom); rows=[]; stats=Counter(); resolved_placements=0
    for tid,count in sorted(counts.items()):
        r=first_animation_calls(rom,tid)
        canonical=[c for c in r['calls'] if c['canonical']]
        sels=sorted({c['selector'] for c in canonical})
        if r['direct_code']: cls='direct_code'
        elif r['truncated']: cls='truncated'
        elif r['bad']: cls='bad'
        elif not canonical: cls='no_canonical_first_animation'
        elif len(sels)==1: cls='unique_selector'
        else: cls='branch_variants'
        stats[cls]+=1
        if sels: resolved_placements += count
        rows.append({'type_id':tid,'placements':count,'initial_archetype_id':tid,'descriptor':f'0x{u32(rom,ARCHETYPE_TABLE+tid*4):06X}','first_animation_selectors':[f'0x{x:04X}' for x in sels],'classification':cls,'states':r['states'],'first_calls':canonical})
    report={'schema':'truerecall.initial_visual_cfg.v1','base_sha1':digest,'method':'CFG traversal with return-stack; stop each path at first VM native 0x1F9A; selector accepted only from canonical immediate push pattern directly preceding call','placed_type_ids':len(counts),'total_placements':sum(counts.values()),'coverage':dict(stats),'resolved_placements':resolved_placements,'types':rows}
    text=json.dumps(report,indent=2,sort_keys=True); print(text)
    if args.json: args.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
