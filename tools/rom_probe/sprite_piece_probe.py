#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
ARCHETYPE_TABLE=0x079906

def u16(b,o): return int.from_bytes(b[o:o+2],'big')
def u32(b,o): return int.from_bytes(b[o:o+4],'big')

def rle128_decode(rom: bytes, off: int) -> tuple[bytes,int]:
    out=bytearray(); p=off
    while True:
        cmd=rom[p]; p+=1
        if cmd==0: break
        if cmd<0x80:
            n=128-cmd; out += rom[p:p+n]; p += n
        else:
            n=256-cmd; value=rom[p]; p+=1; out += bytes([value])*n
        if len(out)>128: raise ValueError(f'RLE overrun at 0x{off:06X}: {len(out)}')
    if len(out)!=128: raise ValueError(f'RLE size at 0x{off:06X}: {len(out)}')
    return bytes(out),p-off

def resolve_chunk(rom: bytes, descriptor: int, piece_word: int):
    vflip=(piece_word>>15)&1; hflip=(piece_word>>14)&1
    group=(piece_word>>8)&0x3F; index=piece_word&0xFF
    source_long=u32(rom,descriptor+2+group*4)
    if source_long & 0x80000000:
        table=source_long & 0x7FFFFFFF
        entry=u16(rom,table+index*2)
        if entry & 0x8000:
            src=table+(entry&0x7FFF); data,encoded_len=rle128_decode(rom,src)
            mode='table_rle'
        else:
            src=table+entry; data=rom[src:src+128]; encoded_len=128; mode='table_raw'
    else:
        src=source_long+index*128; data=rom[src:src+128]; encoded_len=128; mode='contiguous_raw'
    if len(data)!=128: raise ValueError('short chunk')
    return {'vflip':vflip,'hflip':hflip,'group':group,'index':index,'mode':mode,'source':src,'encoded_len':encoded_len,'data':data}

def resolve_record(rom,arch,selector):
    desc=u32(rom,ARCHETYPE_TABLE+arch*4); encoded=u16(rom,desc+selector); alias=encoded&0x0FFE; roff=u16(rom,desc+alias); rec=desc+roff; n=rom[rec+0x0F]
    pieces=[]
    for i in range(n):
        p=rec+0x10+i*4; word=u16(rom,p+2); c=resolve_chunk(rom,desc,word)
        pieces.append({'x':rom[p],'y':rom[p+1],'word':f'0x{word:04X}','vflip':c['vflip'],'hflip':c['hflip'],'group':c['group'],'index':c['index'],'mode':c['mode'],'source':f"0x{c['source']:06X}",'encoded_len':c['encoded_len']})
    return {'archetype':arch,'descriptor':f'0x{desc:06X}','selector':selector,'record_offset':f'0x{roff:04X}','piece_count':n,'pieces':pieces}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('rom',type=Path); ap.add_argument('--json',type=Path); args=ap.parse_args()
    rom=args.rom.read_bytes(); assert len(rom)==EXPECTED_SIZE; digest=hashlib.sha1(rom).hexdigest(); assert digest==EXPECTED_SHA1
    # Renderer anchors: piece count, x/y bytes, resource word/cache key and 128-byte DMA.
    assert rom[0x1123C:0x11240] == bytes.fromhex('1e30200f')
    assert rom[0x1137A:0x113A4] == bytes.fromhex('7400142d00103038f964b540d0440c40010f62000106142d00113238f966b541d2450c4100ef620000f2')
    assert rom[0x113B4:0x113C8] == bytes.fromhex('302d001202403fffd078f9627200123300005341')
    assert rom[0x1142C:0x1146A] == bytes.fromhex('102d0013122d0012d201d201206e002c223010026a1a0881001f2041d040303000006a0e02407fffd0c06100007e6004ef48d240303c00804eb9000132dc')
    # SAT setup uses 0x0500 size bits = 2x2 tiles, preserving low-byte link chain.
    assert rom[0x1171E:0x1173A] == bytes.fromhex('303c05013078f96ab0f8f96e670e1140000352405048b0f8f96e66f2')
    # Micro-codec anchors.
    assert rom[0x114D6:0x114F6] == bytes.fromhex('2278f95a70001018670cd0006400011612184efb000c2238f95a21c9f95a4e75')
    samples=[resolve_record(rom,191,2),resolve_record(rom,166,2),resolve_record(rom,176,2),resolve_record(rom,8,2)]
    report={'schema':'truerecall.sprite_piece.v1','base_sha1':digest,'confirmed':{
      'piece_bytes':4,'piece_format':'byte x_offset, byte y_offset, word flags/group/index','word_bit15':'VDP vertical flip','word_bit14':'VDP horizontal flip','word_bits13_8':'resource group 0..63','word_bits7_0':'resource index 0..255','sprite_size':'fixed 2x2 tiles = 16x16 px','chunk_bytes':128,'chunk_tiles':4,
      'resource_group_table':'descriptor+0x02 + group*4','group_source_positive':'contiguous raw 128-byte chunks','group_source_bit31':'word-offset table; entry bit15 selects RLE versus raw offset','rle':'0=end; 1..127 copy 128-cmd literals; 128..255 repeat next byte 256-cmd times','cache_key':'piece_word & 0x3FFF','cache_slot_tiles':4},'samples':samples}
    text=json.dumps(report,indent=2,sort_keys=True); print(text)
    if args.json: args.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
