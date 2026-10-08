#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from collections import Counter
from pathlib import Path

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
SCENE_TABLE=0x013B4A
SCENE_COUNT=19
PLAYER_DISPATCH=0x003760
PROJECTILE_DISPATCH=0x002C1C
STANDARD_RESOLVE=0x002E18
NOOP=0x002E16

def u16(b,o): return int.from_bytes(b[o:o+2],'big')
def u32(b,o): return int.from_bytes(b[o:o+4],'big')

def player_handlers(rom,n=34):
    out=[]
    for t in range(n):
        p=PLAYER_DISPATCH+t*6
        assert u16(rom,p)==0x4EF9
        out.append(u32(rom,p+2))
    return out

def projectile_handlers(rom,n=34):
    out=[]
    for t in range(n):
        p=PROJECTILE_DISPATCH+t*4
        assert u16(rom,p)==0x6000
        disp=int.from_bytes(rom[p+2:p+4],'big',signed=True)
        out.append((p+2+disp)&0xFFFFFF)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('rom',type=Path); ap.add_argument('--json',type=Path); a=ap.parse_args()
    rom=a.rom.read_bytes(); assert len(rom)==EXPECTED_SIZE
    digest=hashlib.sha1(rom).hexdigest(); assert digest==EXPECTED_SHA1

    assert rom[0x010E2A:0x010E44] == bytes.fromhex('3038fc42d040d04041f900013b4a207000002028000e67000086')
    assert rom[0x010E44:0x010E74] == bytes.fromhex('32680014302900020640003f0240ffc031c0f98aea4831c0f986302900040640003f0240ffc031c0f98cec4831c0f988')
    block=rom[0x010E74:0x010ECE]
    assert bytes.fromhex('21c8f976') in block and bytes.fromhex('31c8f974') in block and bytes.fromhex('3238f9862278f9763038f988') in block
    assert rom[0x010F50:0x011018].find(bytes.fromhex('2478f976')) >= 0
    assert rom[0x010F50:0x011018].find(bytes.fromhex('222d0038')) >= 0
    assert rom[0x010F50:0x011018].find(bytes.fromhex('4e92')) >= 0
    assert rom[NOOP:NOOP+2] == bytes.fromhex('4e75')

    ph=player_handlers(rom); qh=projectile_handlers(rom)
    scenes=[]; type_counts=Counter(); total_records=0; total_cells=0; nonempty_cells=0; total_list_refs=0; max_list=0
    for i in range(SCENE_COUNT):
        rec=u32(rom,SCENE_TABLE+i*4)
        aux=u32(rom,rec+0x0E)
        plane_desc=u32(rom,rec+0x1A)
        width_tiles=u16(rom,plane_desc+4); height_tiles=u16(rom,plane_desc+6)
        width_px=width_tiles*8; height_px=height_tiles*8
        cols=math.ceil(width_px/64); rows=math.ceil(height_px/64)
        count=cols*rows; total_cells+=count
        grid=[u16(rom,aux+j*2) for j in range(count)]
        nonempty_cells += sum(v!=0 for v in grid)
        record_offsets=set(); list_offsets=sorted(set(grid)-{0}); scene_max_list=0
        for lo in list_offsets:
            assert 0 < lo < 0x8000
            vals=[]
            for k in range(256):
                v=u16(rom,aux+lo+k*2); vals.append(v); record_offsets.add(v&0x7FFF)
                if v&0x8000: break
            else: raise AssertionError((i,hex(lo),'unterminated ref list'))
            scene_max_list=max(scene_max_list,len(vals)); total_list_refs+=len(vals)
        max_list=max(max_list,scene_max_list); total_records+=len(record_offsets)
        sc=Counter()
        for ro in record_offsets:
            typ=u16(rom,aux+ro); assert typ < len(ph)
            geom=[u16(rom,aux+ro+o) for o in (2,4,6,8)]
            sc[typ]+=1; type_counts[typ]+=1
            assert len(geom)==4
        scenes.append({
            'scene':i,'scene_record':f'0x{rec:06X}','resource_base':f'0x{aux:06X}',
            'map_tiles':[width_tiles,height_tiles],'map_pixels':[width_px,height_px],
            'grid_cells_64px':[cols,rows],'grid_words':count,'nonempty_cells':sum(v!=0 for v in grid),
            'unique_cell_ref_lists':len(list_offsets),'unique_world_records':len(record_offsets),
            'max_records_per_cell_list':scene_max_list,'world_type_counts':{str(k):v for k,v in sorted(sc.items())}
        })
    used=sorted(type_counts)
    classes={}
    for t in used:
        pt=ph[t]
        classes[str(t)]={
            'records':type_counts[t],
            'player_handler':f'0x{pt:06X}',
            'player_class':'standard_collision_resolution' if pt==STANDARD_RESOLVE else ('ignored_noop' if pt==NOOP else 'special'),
            'projectile_handler':f'0x{qh[t]:06X}',
            'projectile_class':'standard_collision_resolution' if qh[t]==STANDARD_RESOLVE else ('ignored_noop' if qh[t]==NOOP else 'special')
        }
    report={
      'schema':'truerecall.world_spatial_collision.v1','base_sha1':digest,
      'confirmed':{
        'scene_resource_field':'scene_record+0x0E','resource_base_ram':'FFFFF976','row_pointer_table_ram':'FFFFF974',
        'row_stride_bytes_ram':'FFFFF986','row_count_ram':'FFFFF988','cell_size_pixels':[64,64],
        'cell_entry_bytes':2,'cell_entry_semantics':'word offset from resource base to a high-bit-terminated list of world-record offsets',
        'world_record_type_field':'record+0x00','world_record_overlap_words':['record+0x02','record+0x04','record+0x06','record+0x08'],
        'entity_world_callback':'object+0x38','player_dispatch':'0x003750','projectile_dispatch':'0x002C10'
      },
      'retail_summary':{'scenes':SCENE_COUNT,'grid_words':total_cells,'nonempty_grid_cells':nonempty_cells,'unique_world_records_sum':total_records,'cell_record_refs':total_list_refs,'max_records_per_cell_list':max_list,'used_world_types':used,'world_type_counts':{str(k):v for k,v in sorted(type_counts.items())}},
      'world_types':classes,'scenes':scenes,
      'notes':{'geometry_names':'The four overlap words are structurally confirmed but exact axis/order/world-origin labels remain intentionally unresolved.','retail_lists':'Retail data currently has max one record reference per cell list, but the engine loop explicitly supports multiple references before a high-bit terminal entry.'}
    }
    text=json.dumps(report,indent=2,sort_keys=True); print(text)
    if a.json: a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
