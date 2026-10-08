#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from vm_disasm import OPERAND_BYTES,NATIVES,MN
FLOW={'BR_TRUE':0x0000,'BR_FALSE':0x0004,'JMP':0x0008,'CALL':0x000C,'RET_OR_END':0x0010,'SWITCH_D2':0x00AC,'NATIVE':0x00E4}
GEN={v:k for k,v in MN.items()};NATIVE_BY_NAME={v:k for k,v in NATIVES.items()}
def num(s):return int(s,0)
def w(v):return (v&0xFFFF).to_bytes(2,'big')
def l(v):return (v&0xFFFFFFFF).to_bytes(4,'big')
def parse_text(text:str):
 stmts=[]
 for lineno,line in enumerate(text.splitlines(),1):
  line=line.split(';',1)[0].strip()
  if not line:continue
  if line.endswith(':'):stmts.append(('label',line[:-1].strip(),lineno));continue
  parts=line.split(None,1);mn=parts[0];arg=parts[1].strip() if len(parts)>1 else None
  if mn=='.raw':
   stmts.append(('raw',bytes.fromhex(arg.replace(' ','')),lineno));continue
  stmts.append(('ins',(mn,arg),lineno))
 return stmts
def parse(path:Path):return parse_text(path.read_text(encoding='utf-8'))
def ins_size(mn,arg):
 if mn in ('BR_TRUE','BR_FALSE','JMP'):return 4
 if mn=='CALL':return 6
 if mn=='RET_OR_END':return 2
 if mn=='NATIVE':return 6
 if mn=='SWITCH_D2':return 4+4*len([x.strip() for x in arg.split(',') if x.strip()])
 op=int(mn[3:],16) if mn.startswith('OP_') else GEN[mn];return 2+OPERAND_BYTES[op]
def resolve(token,labels):return labels[token] if token in labels else num(token)
def assemble(stmts,base):
 labels={};pc=base
 for kind,obj,lineno in stmts:
  if kind=='label':
   if obj in labels:raise ValueError(f'line {lineno}: duplicate label {obj}')
   labels[obj]=pc
  elif kind=='raw':pc+=len(obj)
  else:
   mn,arg=obj;pc+=ins_size(mn,arg)
 out=bytearray();pc=base
 for kind,obj,lineno in stmts:
  if kind=='label':continue
  if kind=='raw':out+=obj;pc+=len(obj);continue
  mn,arg=obj
  if mn in ('BR_TRUE','BR_FALSE','JMP'):
   op=FLOW[mn];target=resolve(arg,labels);end=pc+4
   if (target&0xFFFF0000)!=(end&0xFFFF0000):raise ValueError('bank-local branch crosses 64K bank')
   enc=w(op)+w(target)
  elif mn=='CALL':enc=w(FLOW[mn])+l(resolve(arg,labels))
  elif mn=='RET_OR_END':enc=w(FLOW[mn])
  elif mn=='NATIVE':
   target=NATIVE_BY_NAME.get(arg,None);target=num(arg) if target is None else target;enc=w(0x00E4)+l(target)
  elif mn=='SWITCH_D2':
   raw_cases=[x.strip() for x in arg.split(',') if x.strip()];cases=[];end=pc+4+4*len(raw_cases)
   for item in raw_cases:
    val_s,tok=item.split(':',1);target=resolve(tok.strip(),labels)
    if (target&0xFFFF0000)!=(end&0xFFFF0000):raise ValueError('switch target crosses 64K bank')
    cases.append((num(val_s.strip()),target))
   enc=w(0x00AC)+w(len(cases))+b''.join(w(v)+w(t) for v,t in cases)
  else:
   op=int(mn[3:],16) if mn.startswith('OP_') else GEN[mn];size=OPERAND_BYTES[op];enc=w(op)
   if size:enc+=num(arg).to_bytes(size,'big')
  out+=enc;pc+=len(enc)
 return bytes(out),labels
