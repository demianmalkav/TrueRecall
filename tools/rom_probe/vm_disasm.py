#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib
from collections import deque
from pathlib import Path

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TYPE_SELECTOR_TABLE=0x07A33C
TYPE_POINTER_TABLE=0x07953E

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

NATIVES={
0x001F9A:'PlayAnimation',
0x001FE4:'AnimationHelper_1FE4',
0x001FF6:'PlayFacingAnimation',
0x00200C:'PlayFacingAnimation13',
0x002022:'PlayDirection24Animation',
0x002038:'ApplyFacingMovement',
0x00204E:'InitArchetypeStats',
0x0020D8:'SpawnLinkedObject',
0x00211C:'SpawnLinkedOffsetObject',
0x002436:'SetArchetype',
0x002448:'PlayFacingAnimationClear',
0x002542:'Native_2542',
0x003B42:'WaitForEventMask',
0x003B9C:'Native_3B9C',
0x00AEF8:'GrantWeapon',
0x00AF08:'ShowMessage',
0x00BC66:'PlayerVisibilityTest',
0x00DAA4:'FireSpreadProjectile',
0x00DB48:'FireStandardProjectile',
0x00DD96:'CommonReaction_DD96',
0x00DE40:'CommonHitDeath_DE40',
}

MN={
0x0014:'LEA_STACK_REL_D1',0x0018:'LEA_CONTEXT_REL_D1',0x001C:'MOVI_W_D2',0x0020:'MOVI_L_D2',
0x0024:'LOAD_ABS_B_D2',0x0028:'LOAD_ABS_W_D2',0x002C:'LOAD_ABSW_SW_D2',0x0030:'LOAD_ABS_L_D2',
0x0034:'LOAD_OBJ_B_D2',0x0038:'LOAD_OBJ_W_D2',0x003C:'LOAD_OBJ_SW_D2',0x0040:'LOAD_OBJ_L_D2',
0x0044:'LOAD_D1_B_D2',0x0048:'LOAD_D1_W_D2',0x004C:'LOAD_D1_SW_D2',0x0050:'LOAD_D1_L_D2',
0x0054:'STORE_ABS_B_D2',0x0058:'STORE_ABS_W_D2',0x005C:'STORE_ABSW_W_D2',0x0060:'STORE_ABS_L_D2',
0x0064:'STORE_OBJ_B_D2',0x0068:'STORE_OBJ_W_D2',0x006C:'STORE_OBJ_L_D2',
0x0070:'STORE_D1_B_D2',0x0074:'STORE_D1_W_D2',0x0078:'STORE_D1W_W_D2',0x007C:'STORE_D1_L_D2',
0x0080:'MOVI_W_D1',0x0084:'MOVI_L_D1',0x0088:'LOAD_D1_W_D1',0x008C:'LOAD_D1_L_D1',
0x0090:'CMP_LT',0x0094:'CMP_LE',0x0098:'CMP_EQ',0x009C:'CMP_GE',0x00A0:'CMP_GT',0x00A4:'CMP_NE',
0x00A8:'SWAP_D1_D2',0x00B0:'AND',0x00B4:'OR',0x00B8:'XOR',0x00C4:'ADD_D1_TO_D2',0x00C8:'SUB_D1_FROM_D2',
0x00D8:'NEG_D2',0x00DC:'NOT_D2',0x00E0:'BOOL_NOT_D2',0x00E8:'SHIFT_D2',0x00EC:'ADJ_NATIVE_STACK',
0x00F0:'PUSH_D2_W',0x00F4:'PUSH_D2_L',0x00F8:'POP_D2_W',0x00FC:'POP_D2_L',
0x0100:'PUSH_D1_W',0x0104:'PUSH_D1_L',0x0108:'POP_D1_W',0x010C:'POP_D1_L',
0x0110:'SCHED_WAIT_D2',0x0114:'SCHED_WAIT_D1_D2',0x0118:'READ_EVENT_D7',0x011C:'ADD_D2_TO_D1',
}

def u16(b,o): return int.from_bytes(b[o:o+2],'big')
def u32(b,o): return int.from_bytes(b[o:o+4],'big')
def bank_target(pc,low): return (pc&0xffff0000)|low

def decode(rom,pc):
    op=u16(rom,pc); p=pc+2
    if op in (0x0000,0x0004,0x0008):
        low=u16(rom,p); p+=2; return {'pc':pc,'op':op,'end':p,'target':bank_target(p,low),'operand':low}
    if op==0x000C:
        t=u32(rom,p); p+=4; return {'pc':pc,'op':op,'end':p,'target':t,'operand':t}
    if op==0x0010:return {'pc':pc,'op':op,'end':p}
    if op==0x00AC:
        count=u16(rom,p);p+=2;cases=[]
        for _ in range(count):
            v=u16(rom,p); t=bank_target(p+4,u16(rom,p+2));p+=4;cases.append((v,t))
        return {'pc':pc,'op':op,'end':p,'cases':cases}
    size=OPERAND_BYTES.get(op)
    if size is None:return {'pc':pc,'op':op,'end':p,'bad':True}
    raw=rom[p:p+size];p+=size
    return {'pc':pc,'op':op,'end':p,'operand':int.from_bytes(raw,'big') if size else None}

def reachable(rom,start,max_states=50000,max_stack=16):
    q=deque([(start,())]); seen=set(); insns={}; labels={start}
    while q and len(seen)<max_states:
        pc,stack=q.popleft();key=(pc,stack)
        if key in seen or not(0<=pc<len(rom)-2):continue
        seen.add(key); ins=decode(rom,pc); insns[pc]=ins
        if ins.get('bad'):continue
        op=ins['op']
        if op in (0,4):
            labels.add(ins['target']);q.append((ins['target'],stack));q.append((ins['end'],stack))
        elif op==8:
            labels.add(ins['target']);q.append((ins['target'],stack))
        elif op==0xC:
            labels.add(ins['target'])
            if len(stack)<max_stack:q.append((ins['target'],stack+(ins['end'],)))
        elif op==0x10:
            if stack:q.append((stack[-1],stack[:-1]))
        elif op==0xAC:
            for _,t in ins['cases']:labels.add(t);q.append((t,stack))
            q.append((ins['end'],stack))
        else:q.append((ins['end'],stack))
    return insns,labels,len(seen)

def fmt(ins):
    op=ins['op']; o=ins.get('operand')
    if op==0x0000:return f'BR_TRUE L_{ins["target"]:06X}'
    if op==0x0004:return f'BR_FALSE L_{ins["target"]:06X}'
    if op==0x0008:return f'JMP L_{ins["target"]:06X}'
    if op==0x000C:return f'CALL L_{ins["target"]:06X}'
    if op==0x0010:return 'RET_OR_END'
    if op==0x00AC:
        return 'SWITCH_D2 ' + ', '.join(f'{v:#06x}:L_{t:06X}' for v,t in ins['cases'])
    if op==0x00E4:
        return 'NATIVE ' + NATIVES.get(o,f'0x{o:06X}')
    name=MN.get(op,f'OP_{op:04X}')
    if o is None:return name
    width=OPERAND_BYTES.get(op,0)
    return f'{name} 0x{o:0{width*2}X}'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--type',type=lambda x:int(x,0));ap.add_argument('--address',type=lambda x:int(x,0));ap.add_argument('--out',type=Path)
    a=ap.parse_args();rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;assert hashlib.sha1(rom).hexdigest()==EXPECTED_SHA1
    if a.type is not None:
        if rom[TYPE_SELECTOR_TABLE+a.type]==0: raise SystemExit(f'type {a.type} is direct-code, not VM scripted')
        start=u32(rom,TYPE_POINTER_TABLE+a.type*4);title=f'type_id {a.type} @ 0x{start:06X}'
    elif a.address is not None:start=a.address;title=f'VM script @ 0x{start:06X}'
    else:raise SystemExit('provide --type or --address')
    insns,labels,states=reachable(rom,start)
    lines=[f'; TrueRecall VM disassembly: {title}',f'; canonical base SHA1 {EXPECTED_SHA1}',f'; reachable instruction addresses: {len(insns)}; traversal states: {states}','']
    for pc in sorted(insns):
        if pc in labels:lines.append(f'L_{pc:06X}:')
        ins=insns[pc]; raw=rom[pc:ins.get('end',pc+2)].hex().upper()
        lines.append(f'  {pc:06X}: {raw:<28} {fmt(ins)}')
    text='\n'.join(lines)+'\n'; print(text,end='')
    if a.out:a.out.write_text(text,encoding='utf-8')
if __name__=='__main__':main()
