#!/usr/bin/env python3
"""Recover the spread-projectile attack family used by retail True Lies actors."""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict,deque
from pathlib import Path
from level_objects_probe import SCENE_COUNT,SCENE_TABLE,lzbeam_decode,u16,u32
from initial_visual_cfg_probe import decode
EXPECTED_SIZE=2_097_152; EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TS=0x07A33C;TP=0x07953E;NATIVE=0x00DAA4;PROJ=0x00AF

def info(rom):
 c=Counter();s=defaultdict(set)
 for si in range(SCENE_COUNT):
  rec=u32(rom,SCENE_TABLE+si*4);d=u32(rom,rec+0xA);n=u16(rom,d);pos=u16(rom,d+2);dec=lzbeam_decode(rom,u32(rom,d+6));rp=d+0xA;t=0;r=[]
  while t<n:st,q=rom[rp],rom[rp+1];rp+=2;r.append((st,q));t+=q
  for st,q in r:
   for _ in range(q):x=u16(dec,pos)&0x3ff;c[x]+=1;s[x].add(si);pos+=st
 return c,s

def calls(rom,tid):
 if rom[TS+tid]==0:return set()
 q=deque([(u32(rom,TP+tid*4),())]);seen=set();out=set()
 while q and len(seen)<50000:
  pc,stack=q.popleft();k=(pc,stack)
  if k in seen or not(0<=pc<len(rom)-2):continue
  seen.add(k);ins=decode(rom,pc)
  if ins.get('bad'):continue
  op=ins['op']
  if op==0xe4:out.add(ins.get('operand'))
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
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
 assert bytes.fromhex('303c00af4eb90000f7cc') in rom[NATIVE:NATIVE+0xA0]
 assert bytes.fromhex('31400064') in rom[NATIVE:NATIVE+0xA0]
 assert rom[TS+PROJ]==0 and u32(rom,TP+PROJ*4)==0x00E3E0
 assert rom[0x00E3EE:0x00E3F6]==bytes.fromhex('2b7c000027ee0034')
 assert rom[0x00E4B6:0x00E4BE]==bytes.fromhex('2b7c00002c100038')
 assert rom[0x079E82+PROJ]==1 and rom[0x079D90+PROJ]==1
 c,s=info(rom);rows=[]
 for tid in sorted(c):
  if NATIVE in calls(rom,tid):rows.append({'type_id':tid,'placements':c[tid],'scenes':sorted(s[tid])})
 assert [x['type_id'] for x in rows]==[20,86]
 report={'schema':'truerecall.spread_attack.v1','base_sha1':digest,'spread_native':'0x00DAA4','projectile_type':PROJ,'projectile_direct_code':'0x00E3E0','projectile_actor_collision':'0x0027EE','projectile_world_collision':'0x002C10','projectile_damage_normal_hard':[1,1],'retail_spread_actor_types':rows,'total_spread_actor_placements':sum(x['placements'] for x in rows)}
 text=json.dumps(report,indent=2,sort_keys=True);print(text)
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
