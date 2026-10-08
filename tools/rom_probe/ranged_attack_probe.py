#!/usr/bin/env python3
"""Recover the shared ranged-fire family used by retail True Lies actors."""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict,deque
from pathlib import Path
from level_objects_probe import SCENE_COUNT,SCENE_TABLE,lzbeam_decode,u16,u32
from initial_visual_cfg_probe import decode
EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TYPE_SELECTOR_TABLE=0x07A33C;TYPE_POINTER_TABLE=0x07953E
RANGED_NATIVE=0x00DB48;PROJECTILE_TYPE=0x00AA

def placement_info(rom):
 c=Counter(); scenes=defaultdict(set)
 for s in range(SCENE_COUNT):
  scene=u32(rom,SCENE_TABLE+s*4);desc=u32(rom,scene+0xA);n=u16(rom,desc);pos=u16(rom,desc+2);dec=lzbeam_decode(rom,u32(rom,desc+6));rp=desc+0xA;total=0;runs=[]
  while total<n:
   st,q=rom[rp],rom[rp+1];rp+=2;assert st in(6,8) and q>0;runs.append((st,q));total+=q
  for st,q in runs:
   for _ in range(q):
    t=u16(dec,pos)&0x3ff;c[t]+=1;scenes[t].add(s);pos+=st
 return c,scenes

def reachable_calls(rom,tid):
 if rom[TYPE_SELECTOR_TABLE+tid]==0:return set()
 start=u32(rom,TYPE_POINTER_TABLE+tid*4);q=deque([(start,())]);seen=set();calls=set()
 while q and len(seen)<50000:
  pc,stack=q.popleft();key=(pc,stack)
  if key in seen or not(0<=pc<len(rom)-2):continue
  seen.add(key);ins=decode(rom,pc)
  if ins.get('bad'):continue
  op=ins['op']
  if op==0x00E4:calls.add(ins.get('operand'))
  if op in(0,4):q.append((ins['target'],stack));q.append((ins['end'],stack))
  elif op==8:q.append((ins['target'],stack))
  elif op==0xC:
   if len(stack)<16:q.append((ins['target'],stack+(ins['end'],)))
  elif op==0x10:
   if stack:q.append((stack[-1],stack[:-1]))
  elif op==0xAC:
   for _,t in ins['cases']:q.append((t,stack))
   q.append((ins['end'],stack))
  else:q.append((ins['end'],stack))
 return calls

def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rom=a.rom.read_bytes()
 assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
 assert bytes.fromhex('303c00aa4eb90000f7cc65164eb900010102') in rom[0x00DB48:0x00DC6C]
 assert rom[TYPE_SELECTOR_TABLE+PROJECTILE_TYPE]==0
 assert u32(rom,TYPE_POINTER_TABLE+PROJECTILE_TYPE*4)==0x00E10E
 assert rom[0x00E11C:0x00E124]==bytes.fromhex('2b7c000027ee0034')
 assert rom[0x00E336:0x00E33E]==bytes.fromhex('2b7c00002c100038')
 assert rom[0x079E82+PROJECTILE_TYPE]==1 and rom[0x079D90+PROJECTILE_TYPE]==1
 counts,scenes=placement_info(rom);shooters=[]
 for tid in sorted(counts):
  if RANGED_NATIVE in reachable_calls(rom,tid):
   shooters.append({'type_id':tid,'placements':counts[tid],'scenes':sorted(scenes[tid])})
 expected=[5,7,24,25,28,38,39,82,98,107,112,126,127]
 assert [x['type_id'] for x in shooters]==expected
 report={'schema':'truerecall.ranged_attack.v1','base_sha1':digest,'ranged_native':'0x00DB48','projectile_type':PROJECTILE_TYPE,'projectile_direct_code':'0x00E10E','projectile_actor_collision':'0x0027EE','projectile_world_collision':'0x002C10','projectile_damage_normal_hard':[1,1],'retail_ranged_actor_types':shooters,'total_ranged_actor_placements':sum(x['placements'] for x in shooters)}
 text=json.dumps(report,indent=2,sort_keys=True);print(text)
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
