#!/usr/bin/env python3
"""TrueRecall Beam LZ codec.

Decoder follows the retail format. Encoder emits valid streams using greedy
absolute-output backreferences and literal runs; it does not attempt to reproduce
Beam's original compressor byte-for-byte.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from pathlib import Path


def u16(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+2], "big")


def decode_stream(buf: bytes, off: int = 0) -> bytes:
    out_len = u16(buf, off); command_offset = u16(buf, off + 2)
    read_pos = off + 4; command_pos = off + command_offset + 2
    bits_left = 0; current = 0; out = bytearray()

    def bit() -> int:
        nonlocal command_pos, bits_left, current
        if bits_left == 0:
            current = buf[command_pos]; command_pos += 1; bits_left = 8
        value = (current >> 7) & 1; current = (current << 1) & 0xFF; bits_left -= 1
        return value

    def bits(count: int) -> int:
        value = 0
        for _ in range(count): value = (value << 1) | bit()
        return value

    def count() -> int:
        value = 1
        while bit() == 0: value = (value << 1) | bit()
        return value

    n = count(); out.extend(buf[read_pos:read_pos+n]); read_pos += n
    while len(out) < out_len:
        written = len(out)
        index_bits = written.bit_length() if written < 256 else 8 + (written >> 8).bit_length()
        source = bits(index_bits); n = count() + 2
        if source >= len(out): raise ValueError(f"invalid backref source {source} at out {len(out)}")
        for i in range(n):
            out.append(out[source + i])
            if len(out) >= out_len: break
        if len(out) < out_len and bit() == 0:
            n = count(); out.extend(buf[read_pos:read_pos+n]); read_pos += n
    return bytes(out[:out_len])


def encode_count(n: int) -> list[int]:
    if n < 1: raise ValueError("count must be >=1")
    bits = []
    for c in bin(n)[3:]: bits.extend((0, 1 if c == "1" else 0))
    bits.append(1)
    return bits


def emit_fixed(bits: list[int], value: int, width: int) -> None:
    if value < 0 or value >= (1 << width): raise ValueError((value, width))
    bits.extend((value >> shift) & 1 for shift in range(width - 1, -1, -1))


def pack_bits(bits: list[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        value = 0; chunk = bits[i:i+8]
        for b in chunk: value = (value << 1) | b
        value <<= 8 - len(chunk); out.append(value)
    return bytes(out)


def encode_stream(data: bytes, max_candidates: int = 128) -> bytes:
    if not data: raise ValueError("zero-length stream unsupported by retail count code")
    if len(data) > 0xFFFF: raise ValueError("format stores uncompressed length as a word")
    if len(data) == 1:
        payload = data; bits = encode_count(1)
        return len(data).to_bytes(2,"big") + (len(payload)+2).to_bytes(2,"big") + payload + pack_bits(bits)

    index: dict[bytes, list[int]] = defaultdict(list); indexed_until = -1
    def add_through(last: int) -> None:
        nonlocal indexed_until
        last = min(last, len(data) - 3)
        while indexed_until < last:
            indexed_until += 1; key = data[indexed_until:indexed_until+3]; lst = index[key]; lst.append(indexed_until)
            if len(lst) > max_candidates: del lst[:-max_candidates]

    def match_at(pos: int):
        if pos + 3 > len(data): return None
        add_through(pos - 1); candidates = index.get(data[pos:pos+3], ())
        best_src = -1; best_len = 0
        for src in reversed(candidates):
            if src >= pos: continue
            k = 3
            while pos + k < len(data) and data[src + k] == data[pos + k]:
                k += 1
                if src + k >= len(data): break
            if k > best_len: best_src, best_len = src, k
        return (best_src, best_len) if best_len >= 3 else None

    bits: list[int] = []; payload = bytearray(); pos = 1; add_through(0)
    while pos < len(data) and match_at(pos) is None:
        add_through(pos); pos += 1
    payload.extend(data[:pos]); bits.extend(encode_count(pos))

    while pos < len(data):
        match = match_at(pos)
        if match is None:
            lit_start = pos
            while pos < len(data) and match_at(pos) is None:
                add_through(pos); pos += 1
            bits.append(0); bits.extend(encode_count(pos - lit_start)); payload.extend(data[lit_start:pos])
            if pos >= len(data): break
            match = match_at(pos)
        src, n = match; written = pos
        width = written.bit_length() if written < 256 else 8 + (written >> 8).bit_length()
        emit_fixed(bits, src, width); bits.extend(encode_count(n - 2)); pos += n; add_through(pos - 1)
        if pos >= len(data): break
        if match_at(pos) is not None:
            bits.append(1); continue
        bits.append(0); lit_start = pos
        while pos < len(data) and match_at(pos) is None:
            add_through(pos); pos += 1
        bits.extend(encode_count(pos - lit_start)); payload.extend(data[lit_start:pos])

    command_bits = pack_bits(bits); command_offset = len(payload) + 2
    if command_offset > 0xFFFF: raise ValueError("literal payload too large for command offset")
    encoded = len(data).to_bytes(2,"big") + command_offset.to_bytes(2,"big") + bytes(payload) + command_bits
    assert decode_stream(encoded) == data
    return encoded


def main() -> None:
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    enc = sub.add_parser("encode"); enc.add_argument("input", type=Path); enc.add_argument("output", type=Path)
    dec = sub.add_parser("decode"); dec.add_argument("input", type=Path); dec.add_argument("output", type=Path); dec.add_argument("--offset", type=lambda x:int(x,0), default=0)
    args = ap.parse_args()
    if args.cmd == "encode":
        raw = args.input.read_bytes(); out = encode_stream(raw); args.output.write_bytes(out); print(f"{len(raw)} -> {len(out)} bytes ({len(out)/len(raw):.3f}x)")
    else:
        out = decode_stream(args.input.read_bytes(), args.offset); args.output.write_bytes(out); print(len(out))

if __name__ == "__main__": main()
