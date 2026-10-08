#!/usr/bin/env python3
"""Beam LZ codec used by True Lies.

The decoder follows the retail format. The encoder emits compatible streams using
absolute-output backreferences and literal runs. It is deterministic but does not
attempt to reproduce Beam's original compressor bit-for-bit.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def decode_stream(buf: bytes, off: int = 0) -> bytes:
    out_len = u16(buf, off)
    command_offset = u16(buf, off + 2)
    read_pos = off + 4
    command_pos = off + command_offset + 2
    bits_left = 0
    current = 0
    out = bytearray()

    def bit() -> int:
        nonlocal command_pos, bits_left, current
        if bits_left == 0:
            current = buf[command_pos]
            command_pos += 1
            bits_left = 8
        value = (current >> 7) & 1
        current = (current << 1) & 0xFF
        bits_left -= 1
        return value

    def bits(count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | bit()
        return value

    def count() -> int:
        value = 1
        while bit() == 0:
            value = (value << 1) | bit()
        return value

    literal_count = count()
    out.extend(buf[read_pos:read_pos + literal_count])
    read_pos += literal_count

    while len(out) < out_len:
        written = len(out)
        index_bits = written.bit_length() if written < 256 else 8 + (written >> 8).bit_length()
        source = bits(index_bits)
        copy_count = count() + 2
        if source >= len(out):
            raise ValueError(f"invalid backreference source {source} at output {len(out)}")
        for i in range(copy_count):
            out.append(out[source + i])
            if len(out) >= out_len:
                break
        if len(out) < out_len and bit() == 0:
            literal_count = count()
            out.extend(buf[read_pos:read_pos + literal_count])
            read_pos += literal_count

    return bytes(out[:out_len])


def encode_count(value: int) -> list[int]:
    if value < 1:
        raise ValueError("count must be >= 1")
    result: list[int] = []
    for digit in bin(value)[3:]:
        result.extend((0, 1 if digit == "1" else 0))
    result.append(1)
    return result


def emit_fixed(bits: list[int], value: int, width: int) -> None:
    if not 0 <= value < (1 << width):
        raise ValueError((value, width))
    bits.extend((value >> shift) & 1 for shift in range(width - 1, -1, -1))


def pack_bits(bits: list[int]) -> bytes:
    output = bytearray()
    for pos in range(0, len(bits), 8):
        chunk = bits[pos:pos + 8]
        value = 0
        for item in chunk:
            value = (value << 1) | item
        value <<= 8 - len(chunk)
        output.append(value)
    return bytes(output)


def encode_stream(data: bytes, max_candidates: int = 128) -> bytes:
    """Encode one LZBeam block with a deterministic greedy match finder."""
    if not data:
        raise ValueError("zero-length stream is not representable by the retail count code")
    if len(data) > 0xFFFF:
        raise ValueError("format stores the decompressed length as one word")

    index: dict[bytes, list[int]] = defaultdict(list)
    indexed_until = -1

    def add_through(last: int) -> None:
        nonlocal indexed_until
        last = min(last, len(data) - 3)
        while indexed_until < last:
            indexed_until += 1
            key = data[indexed_until:indexed_until + 3]
            positions = index[key]
            positions.append(indexed_until)
            if len(positions) > max_candidates:
                del positions[:-max_candidates]

    def match_at(pos: int):
        if pos + 3 > len(data):
            return None
        add_through(pos - 1)
        candidates = index.get(data[pos:pos + 3], ())
        best_source = -1
        best_length = 0
        for source in reversed(candidates):
            if source >= pos:
                continue
            length = 3
            # Retail backreferences may overlap their own output. Comparing against
            # the known target bytes models the same repeating-copy behavior.
            while pos + length < len(data) and source + length < len(data) and data[source + length] == data[pos + length]:
                length += 1
            if length > best_length:
                best_source, best_length = source, length
        return (best_source, best_length) if best_length >= 3 else None

    payload = bytearray()
    command_bits: list[int] = []

    # The initial literal run is mandatory and non-empty.
    pos = 1
    add_through(0)
    while pos < len(data) and match_at(pos) is None:
        add_through(pos)
        pos += 1
    payload.extend(data[:pos])
    command_bits.extend(encode_count(pos))

    while pos < len(data):
        match = match_at(pos)
        if match is None:
            # Defensive path; normal flow reaches literals immediately after a copy.
            literal_start = pos
            while pos < len(data) and match_at(pos) is None:
                add_through(pos)
                pos += 1
            command_bits.append(0)
            command_bits.extend(encode_count(pos - literal_start))
            payload.extend(data[literal_start:pos])
            if pos >= len(data):
                break
            match = match_at(pos)

        source, length = match
        written = pos
        index_bits = written.bit_length() if written < 256 else 8 + (written >> 8).bit_length()
        emit_fixed(command_bits, source, index_bits)
        command_bits.extend(encode_count(length - 2))
        pos += length
        add_through(pos - 1)
        if pos >= len(data):
            break

        if match_at(pos) is not None:
            command_bits.append(1)  # next token is another backreference
            continue

        command_bits.append(0)  # literal run follows
        literal_start = pos
        while pos < len(data) and match_at(pos) is None:
            add_through(pos)
            pos += 1
        command_bits.extend(encode_count(pos - literal_start))
        payload.extend(data[literal_start:pos])

    commands = pack_bits(command_bits)
    command_offset = len(payload) + 2
    if command_offset > 0xFFFF:
        raise ValueError("literal payload is too large for the command offset word")

    return (
        len(data).to_bytes(2, "big")
        + command_offset.to_bytes(2, "big")
        + bytes(payload)
        + commands
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    enc = sub.add_parser("encode")
    enc.add_argument("input", type=Path)
    enc.add_argument("output", type=Path)
    dec = sub.add_parser("decode")
    dec.add_argument("input", type=Path)
    dec.add_argument("output", type=Path)
    dec.add_argument("--offset", type=lambda value: int(value, 0), default=0)
    args = ap.parse_args()

    if args.command == "encode":
        raw = args.input.read_bytes()
        encoded = encode_stream(raw)
        assert decode_stream(encoded) == raw
        args.output.write_bytes(encoded)
        print(f"{len(raw)} -> {len(encoded)} bytes ({len(encoded) / len(raw):.3f}x)")
    else:
        decoded = decode_stream(args.input.read_bytes(), args.offset)
        args.output.write_bytes(decoded)
        print(len(decoded))


if __name__ == "__main__":
    main()
