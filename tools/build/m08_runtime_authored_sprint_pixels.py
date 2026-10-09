#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
BASE='d39174bed46ede85531b86df7ba49123ce2f8411';OLD=0x200000;NEW=0x400000;CHECK=0x18E;ROM_END=0x1A4
DIR_SRC=0x13F32;DIR_DST=0x200000;DIR_SIZE=0x2000;SPRINT_BASE=0x1FF0;REFS=[0x19AE,0x1A24,0x1A80,0x1AA4,0x1B0E,0x1B32]
AH=0x83A6;MH=0x9864;AT=0x207000;MT=0x207080;ORIG=bytes.fromhex('08380006FB7F')
PLAYER_DESC=0x0F0000;GROUP0_TABLE=0x0E5B9E;RAW_BANK=0x210000
KEY_HOOK=0x113B4;KEY_ORIG=bytes.fromhex('302d001202403fff');KT=0x208100
RENDER_HOOK=0x1143C;RENDER_ORIG=bytes.fromhex('223010026a1a');RT=0x208000

def u16(b,o):return int.from_bytes(b[o:o+2],'big')
def jmp(a):return b'\x4e\xf9'+a.to_bytes(4,'big')
def checksum(b):
 s=0
 for i in range(0x200,len(b)-1,2):s=(s+int.from_bytes(b[i:i+2],'big'))&0xffff
 return s
def rle128(rom,off):
 out=bytearray();p=off
 while True:
  cmd=rom[p];p+=1
  if cmd==0:break
  if cmd<0x80:n=128-cmd;out+=rom[p:p+n];p+=n
  else:n=256-cmd;v=rom[p];p+=1;out+=bytes([v])*n
  if len(out)>128:return None
 return bytes(out) if len(out)==128 else None
def chunk(rom,i):
 e=u16(rom,GROUP0_TABLE+i*2)
 if e&0x8000:return rle128(rom,GROUP0_TABLE+(e&0x7fff))
 a=GROUP0_TABLE+e;return rom[a:a+128] if a+128<=len(rom) else None

def build(raw):
 assert len(raw)==OLD and hashlib.sha1(raw).hexdigest()==BASE
 assert raw[KEY_HOOK:KEY_HOOK+8]==KEY_ORIG and raw[RENDER_HOOK:RENDER_HOOK+6]==RENDER_ORIG
 b=bytearray(raw)+bytearray([0xff])*(NEW-OLD);b[ROM_END:ROM_END+4]=(NEW-1).to_bytes(4,'big')
 b[DIR_DST:DIR_DST+DIR_SIZE]=raw[DIR_SRC:DIR_SRC+DIR_SIZE]
 for p in REFS:b[p:p+4]=DIR_DST.to_bytes(4,'big')
 b[DIR_DST+SPRINT_BASE:DIR_DST+SPRINT_BASE+16]=raw[DIR_SRC+0xF2:DIR_SRC+0xF2+16]
 anim=bytes.fromhex('08380005F6EC670A303C1FF0')+jmp(0x83C2)+ORIG+jmp(0x83AC)
 move=bytes.fromhex('08380005F6EC6714303C0300323C02804EB900009D8A')+jmp(0x97FA)+ORIG+jmp(0x986A)
 b[AT:AT+len(anim)]=anim;b[MT:MT+len(move)]=move;b[AH:AH+6]=jmp(AT);b[MH:MH+6]=jmp(MT)
 invalid=[]
 for i in range(256):
  c=chunk(raw,i)
  if c is None or len(c)!=128:invalid.append(i);c=bytes(128)
  else:
   c=bytearray(c);c[0:8]=bytes([0xFF])*8;c=bytes(c)
  b[RAW_BANK+i*128:RAW_BANK+(i+1)*128]=c
 # While Y is held, the runtime-validated avatar descriptor receives an isolated cache namespace.
 keytr=(bytes.fromhex('302D0012')+bytes.fromhex('02403FFF')+bytes.fromhex('08380005F6EC')+bytes.fromhex('6718')+
        bytes.fromhex('2F08')+bytes.fromhex('206E002C')+bytes.fromhex('B1FC')+PLAYER_DESC.to_bytes(4,'big')+bytes.fromhex('205F')+
        bytes.fromhex('6608')+bytes.fromhex('024000FF')+bytes.fromhex('00403F00')+jmp(0x113BC))
 assert len(keytr)==46
 b[KT:KT+len(keytr)]=keytr;b[KEY_HOOK:KEY_HOOK+8]=jmp(KT)+bytes.fromhex('4E71')
 # Replay the retail source lookup and substitute the authored raw bank only for that avatar/Y path.
 rendertr=(bytes.fromhex('22301002')+
          bytes.fromhex('08380005F6EC')+bytes.fromhex('6716')+
          bytes.fromhex('2F08')+bytes.fromhex('206E002C')+bytes.fromhex('B1FC')+PLAYER_DESC.to_bytes(4,'big')+bytes.fromhex('205F')+
          bytes.fromhex('6606')+bytes.fromhex('223C')+RAW_BANK.to_bytes(4,'big')+
          bytes.fromhex('4A81')+bytes.fromhex('6B06')+jmp(0x1145C)+jmp(0x11442))
 assert len(rendertr)==50, len(rendertr)
 b[RT:RT+len(rendertr)]=rendertr;b[RENDER_HOOK:RENDER_HOOK+6]=jmp(RT)
 b[CHECK:CHECK+2]=b'\0\0';cs=checksum(b);b[CHECK:CHECK+2]=cs.to_bytes(2,'big')
 rep={'schema':'truerecall.m08.runtime_authored_sprint.v1','base_sha1':BASE,'output_sha1':hashlib.sha1(b).hexdigest(),'rom_size':NEW,
      'cache_namespace':'0x3F00 | index','scope_test':'runtime-validated avatar descriptor 0x0F0000 while Y held','raw_bank':hex(RAW_BANK),'authored_pixel_rule':'valid chunks bytes0..7 -> FF','checksum':f'0x{cs:04X}'}
 return bytes(b),rep
if __name__=='__main__':
 ap=argparse.ArgumentParser(description='Build runtime-validated 4 MiB sprint with authored avatar sprite pixels.');ap.add_argument('rom',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--report',type=Path);a=ap.parse_args();o,r=build(a.rom.read_bytes());a.out.write_bytes(o);t=json.dumps(r,indent=2);print(t);a.report and a.report.write_text(t+'\n')
