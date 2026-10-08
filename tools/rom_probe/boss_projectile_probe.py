#!/usr/bin/env python3
"""Validate the scene-17 boss-class projectile chain (type 104 -> runtime 225)."""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict,deque
from pathlib import Path
from level_objects_probe import SCENE_COUNT,SCENE_TABLE,lzbeam_decode,u16,u32
from initial_visual_cfg_probe import decode
EXPECTED_SIZE=2_097_152;SHA='d39174bed46ede85531b86df7ba49123ce2f8411';TS=0x7A33C;TP=0x7953E
PARENT=104;CHILD=225;SPAWN_NATIVE=0x211C

def placements(rom):
 c=Counter();s=defaultdict(set)
 for si in range(SCENE_COUNT):
  rec=u32(rom,SCENE_TABLE+si*4);d=u32(rom,rec+0xA);n=u16(rom,d);pos=u16(rom,d+2);dec=lzbeam_decode(rom,u32(rom,d+6));rp=d+0xA;t=0;r=[]
  while t<n:st,q=rom[rp],rom[rp+1];rp+=2;r.append((st,q));t+=q
  for st,q in r:
   for _ in range(q):x=u16(dec,pos)&0x3ff;c[x]+=1;s[x].add(si);pos+=st
 return c,s

def child_spawns(rom,tid):
 q=deque([(u32(rom,TP+tid*4),())]);seen=set();out=[]
 while q and len(seen)<100000:
  pc,stack=q.popleft();k=(pc,stack)
  if k in seen or not(0<=pc<len(rom)-2):continue
  seen.add(k);ins=decode(rom,pc)
  if ins.get('bad'):continue
  op=ins['op']
  if op==0xe4 and ins.get('operand')==SPAWN_NATIVE:
   if pc>=6 and u16(rom,pc-6)==0x1c and u16(rom,pc-2)==0xf0:out.append(u16(rom,pc-4))
  if op in(0,4):q.append((ins['target'],stack));q.append((ins['end'],stack))
  elif op==8:q.append((ins['target'],stack))
  elif op==0xc:
   if len(stack)<16:q.append((ins['target'],stack+(ins['end'],)))
  elif op==0x10:
   if stack:q.append((stack[-1],stack[:-1]))
  elif op==0xac:
   for _,x in ins['cases']:q.append((x,stack))
   q.append((ins['end'],stack))
  else:q.append((ins['end'],stack))
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;dg=hashlib.sha1(rom).hexdigest();assert dg==SHA
 c,s=placements(rom);assert c[PARENT]==1 and sorted(s[PARENT])==[17]
 assert rom[0x7A066+PARENT]==100 and rom[0x79F74+PARENT]==100
 sp=child_spawns(rom,PARENT);assert sp and set(sp)=={CHILD}
 assert rom[TS+CHILD]==1 and u32(rom,TP+CHILD*4)==0x12FF54
 assert bytes.fromhex('0084000027ee00a8006c0034') in rom[0x12FF54:0x130040]
 assert bytes.fromhex('00e4000021da') in rom[0x12FF54:0x130040]
 assert rom[0x21DA:0x21E2]==bytes.fromhex('304d4eb9000127f0')
 assert rom[0x79E82+CHILD]==1 and rom[0x79D90+CHILD]==1
 rep={'schema':'truerecall.boss_projectile.v1','base_sha1':dg,'parent_type':PARENT,'parent_placements':1,'parent_scenes':[17],'parent_hp_normal_hard':[100,100],'spawn_native':'0x00211C','runtime_projectile_type':CHILD,'projectile_script':'0x12FF54','projectile_actor_collision':'0x0027EE','projectile_velocity_helper':'0x0127F0','projectile_damage_normal_hard':[1,1],'classification':'boss_class_ranged_actor','proper_name_status':'unresolved'}
 text=json.dumps(rep,indent=2,sort_keys=True);print(text)
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
