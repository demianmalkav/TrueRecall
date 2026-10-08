#!/usr/bin/env python3
"""Validate the destructible loot-crate class (retail type 113)."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from level_objects_probe import u32
EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TS=0x07A33C;TP=0x07953E;TYPE=113

def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rom=a.rom.read_bytes()
 assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
 assert rom[TS+TYPE]==1
 start=u32(rom,TP+TYPE*4);assert start==0x17C84A
 blob=rom[start:start+0x500]
 # Initial visual selector 0x005E.
 assert bytes.fromhex('001c005e00f0001c000000f000e400001f9a') in blob
 # Destruction/damage state: actor callback 0x2828 and lifecycle archetype 176 (0x00B0).
 assert bytes.fromhex('00840000282800a8006c0034') in blob
 assert bytes.fromhex('001c00b000f000e400002436') in blob
 # Conditional drops created through spawn_linked_init: type68 shotgun ammo or type54 health.
 assert bytes.fromhex('001c004400f000e4000020d8') in blob
 assert bytes.fromhex('001c003600f000e4000020d8') in blob
 # Initial archetype stats.
 assert rom[0x07A066+TYPE]==1 and rom[0x079F74+TYPE]==1
 assert rom[0x079E82+TYPE]==6 and rom[0x079D90+TYPE]==10
 report={'schema':'truerecall.loot_crate.v1','base_sha1':digest,'type_id':TYPE,'classification':'destructible_loot_supply_crate','initial_selector':'0x005E','hp_normal_hard':[1,1],'damage_normal_hard':[6,10],'damage_callback':'0x002828','destruction_archetype':176,'conditional_drop_type_ids':[68,54],'conditional_drop_labels':['shotgun_ammo_pickup','health_pickup'],'spawn_native':'0x0020D8'}
 text=json.dumps(report,indent=2,sort_keys=True);print(text)
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
