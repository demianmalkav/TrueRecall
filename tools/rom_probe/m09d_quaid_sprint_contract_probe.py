#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

CANON='d39174bed46ede85531b86df7ba49123ce2f8411'
DESC=0x0A0000; DIR_TABLE=0x013F32; ROW=0x00F2
FACINGS=['N','NE','E','SE','S','SW','W','NW']; PHASES=[0,2,4,6,8,10]
EXPECTED_BASES=[0x0C2A,0x0C36,0x0C4E,0x0C66,0x0C7E,0x0C72,0x0C5A,0x0C42]
AUTHORED=['N','NE','E','SE','S']; MIRRORS={'SW':'SE','W':'E','NW':'NE'}

def word(b,o):return int.from_bytes(b[o:o+2],'big')
def parse_record(rom,off):
 r=DESC+off; vals=[word(rom,r+i) for i in range(0,14,2)]; n=rom[r+15];pieces=[]
 for j in range(n):
  p=r+0x10+j*4; pw=word(rom,p+2);pieces.append({'local_x':rom[p]-15,'local_y':rom[p+1]-15,'piece_word':f'0x{pw:04X}','group':(pw>>8)&0x3F,'chunk_index':pw&0xFF})
 return {'offset':f'0x{off:04X}','address':f'0x{r:06X}','origin_x':vals[3],'origin_y':vals[4],'clip_width':vals[5],'clip_height':vals[6],'piece_count':n,'pieces':pieces}

def analyze(rom):
 if len(rom)!=0x200000 or hashlib.sha1(rom).hexdigest()!=CANON:raise ValueError('wrong canonical ROM')
 bases=[word(rom,DIR_TABLE+ROW+i*2) for i in range(8)]
 if bases!=EXPECTED_BASES:raise ValueError(('direction row changed',bases))
 states=[];records={};groups=set();indices=set()
 for face,base in zip(FACINGS,bases):
  for delta in PHASES:
   sel=base+delta;enc=word(rom,DESC+sel);alias=enc&0x0FFE;off=word(rom,DESC+alias);rec=parse_record(rom,off);records.setdefault(rec['offset'],rec)
   for p in rec['pieces']:groups.add(p['group']);indices.add(p['chunk_index'])
   states.append({'facing':face,'phase_delta':delta,'selector':f'0x{sel:04X}','encoded':f'0x{enc:04X}','record_offset':rec['offset'],'encoded_hflip_bit':bool(enc&0x4000)})
 if len(records)!=10:raise ValueError('expected 10 unique records')
 if groups!={7}:raise ValueError(groups)
 if indices!=set(range(0x68,0x80)):raise ValueError(sorted(indices))
 by={(s['facing'],s['phase_delta']):s for s in states}
 for mirror,src in MIRRORS.items():
  for d in PHASES:
   a=by[(src,d)];m=by[(mirror,d)]
   if a['record_offset']!=m['record_offset'] or a['encoded_hflip_bit'] or not m['encoded_hflip_bit']:raise ValueError(('mirror contract',src,mirror,d,a,m))
 direction={}
 for face in FACINGS:
  fs=[s for s in states if s['facing']==face]
  direction[face]={'base_selector':f'0x{bases[FACINGS.index(face)]:04X}','record_offsets':[s['record_offset'] for s in fs],'chunk_indices':sorted({p['chunk_index'] for s in fs for p in records[s['record_offset']]['pieces']}),'mirrors':MIRRORS.get(face)}
 maxpieces=max(r['piece_count'] for r in records.values()); maxclip=[max(r['clip_width'] for r in records.values()),max(r['clip_height'] for r in records.values())]
 return {'schema':'truerecall.m09d.quaid_sprint_contract.v1','canonical_sha1':CANON,'descriptor':'0x000A0000','direction_table':'0x013F32','source_row':'0x00F2','phase_deltas':PHASES,'direction_bases':[f'0x{x:04X}' for x in bases],'authored_direction_families':AUTHORED,'mirrored_direction_families':MIRRORS,'unique_mapping_records':len(records),'resource_groups':sorted(groups),'chunk_index_range':['0x68','0x7F'],'unique_retail_chunk_indices':len(indices),'records':records,'directions':direction,'production_budget_v1':{'native_phases_per_direction':6,'authored_direction_families':5,'runtime_facings':8,'max_retail_piece_count_per_frame':maxpieces,'max_retail_clip_width':maxclip[0],'max_retail_clip_height':maxclip[1],'reserved_chunk_slots_per_phase':24,'reserved_chunk_bytes_per_phase':24*128,'six_phase_reserved_chunk_bytes':6*24*128,'transparent_palette_index':0,'palette_indices':[0,15],'policy':'preserve retail mapping geometry and chunk-slot identities for first production Quaid family; author pixels into the 24 proven group-7 slots before considering new mapping geometry'}}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rep=analyze(a.rom.read_bytes());text=json.dumps(rep,indent=2)+'\n';print(text,end='')
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text)
if __name__=='__main__':main()
