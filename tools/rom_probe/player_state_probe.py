#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

CANONICAL_SHA1 = 'd39174bed46ede85531b86df7ba49123ce2f8411'

WRITE_OPS = {
    b'\x31\xfc': ('MOVEI.W', 6),
    b'\x42\x78': ('CLR.W', 4),
    b'\x00\x78': ('ORI.W', 6),
    b'\x02\x78': ('ANDI.W', 6),
    b'\x0a\x78': ('EORI.W', 6),
}

def hex0(x): return f'0x{x:06X}'

def scan_word_writes(rom: bytes, addr: int):
    out=[]
    for i in range(len(rom)-6):
        op=rom[i:i+2]
        if op not in WRITE_OPS: continue
        name,n=WRITE_OPS[op]
        if name=='CLR.W':
            if int.from_bytes(rom[i+2:i+4],'big')==addr:
                out.append({'rom':hex0(i),'op':name,'value':0})
        else:
            if int.from_bytes(rom[i+4:i+6],'big')==addr:
                out.append({'rom':hex0(i),'op':name,'value':int.from_bytes(rom[i+2:i+4],'big')})
    return out

def find_all(rom: bytes, pat: bytes, limit=0x200000):
    out=[]; pos=0
    while True:
        i=rom.find(pat,pos)
        if i<0: break
        if i<limit: out.append(i)
        pos=i+1
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('--json', action='store_true')
    ns=ap.parse_args()
    rom=ns.rom.read_bytes()
    sha1=hashlib.sha1(rom).hexdigest()
    if sha1 != CANONICAL_SHA1:
        raise SystemExit(f'wrong base ROM SHA-1: {sha1}')

    result={
      'sha1':sha1,
      'controller_history':{
        'range':'0xFFFFF6EA..0xFFFFF6F0',
        'routine_region':'0x012B60..0x012BC8',
        'F6EA':'previous controller word',
        'F6EC':'current controller word',
        'F6EE':'newly-activated/rising-edge word',
        'F6F0':'bits active in consecutive samples',
        'evidence':'previous F6EC copied to F6EA; new read stored to F6EC; (old XOR new) AND new stored to F6EE; old AND new stored to F6F0',
      },
      'gameplay_bitfields':{},
      'anchors':{
        'player_control_dispatch':'0x009780..0x0098BA',
        'illegal_control_string':'0x009892',
        'input_poll_pipeline':'0x012B60..0x012BC8',
      }
    }
    for a in (0xFB7C,0xFB7E):
        result['gameplay_bitfields'][f'{a:04X}'] = scan_word_writes(rom,a)

    result['refs']={
      'F6EC':[hex0(x) for x in find_all(rom,b'\xF6\xEC') if x<0x14000],
      'F6EE':[hex0(x) for x in find_all(rom,b'\xF6\xEE') if x<0x14000],
      'FB7C':[hex0(x) for x in find_all(rom,b'\xFB\x7C') if x<0x14000],
      'FB7E':[hex0(x) for x in find_all(rom,b'\xFB\x7E') if x<0x14000],
    }
    if ns.json:
        print(json.dumps(result,indent=2))
    else:
        print('TrueRecall player-state probe')
        print('SHA-1:',sha1)
        print('controller:', result['controller_history'])
        for k,v in result['gameplay_bitfields'].items():
            print(k, v)

if __name__=='__main__': main()
