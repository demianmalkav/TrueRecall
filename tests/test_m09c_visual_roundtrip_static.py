#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "rom_probe"))
sys.path.insert(0, str(TOOLS / "build"))
sys.path.insert(0, str(TOOLS))

from m09c_visual_avatar_roundtrip_probe import (
    VISUAL_DESCRIPTOR,
    compiler_frame,
    reconstruct_compiled,
    record_info,
)
from sprite_sequence_compiler import compile_sequence


def p16(value: int) -> bytes:
    return int(value & 0xFFFF).to_bytes(2, "big")


def p32(value: int) -> bytes:
    return int(value).to_bytes(4, "big")


def synthetic_visual_descriptor_rom() -> bytes:
    rom = bytearray(2_097_152)
    desc = VISUAL_DESCRIPTOR

    # Packed descriptor contract:
    #   desc+0x00 -> record offset used after alias resolution
    #   desc+0x02 -> group-0 long source pointer
    # Selector 0x0002 therefore reads the high word of that group pointer as its
    # encoded entry. A source pointer below 0x00020000 gives encoded=0x0001,
    # alias=(0x0001 & 0x0FFE)=0, which resolves through desc+0x00.
    record_offset = 0x0100
    chunk_source = 0x00010300
    rom[desc:desc + 2] = p16(record_offset)
    rom[desc + 2:desc + 6] = p32(chunk_source)

    record = desc + record_offset
    header_words = [0x0001, 0x0002, 0x0003, 0x0064, 0x00C8, 0x0010, 0x0010]
    cursor = record
    for value in header_words:
        rom[cursor:cursor + 2] = p16(value)
        cursor += 2
    rom[record + 0x0E] = 0x40
    rom[record + 0x0F] = 1
    rom[record + 0x10:record + 0x14] = bytes([15, 15, 0, 0])

    # One raw 16x16 chunk (four Genesis tiles), all pixels palette index 1.
    rom[chunk_source:chunk_source + 128] = bytes([0x11]) * 128
    return bytes(rom)


class M09CVisualRoundtripStaticTest(unittest.TestCase):
    def test_packed_selector_and_group_pointer_contract(self) -> None:
        rom = synthetic_visual_descriptor_rom()
        info = record_info(rom, VISUAL_DESCRIPTOR, 0x0002)
        self.assertEqual(info["encoded_entry"], 0x0001)
        self.assertEqual(info["alias_offset"], 0)
        self.assertEqual(info["record_offset"], 0x0100)
        self.assertEqual(info["piece_count"], 1)
        self.assertEqual(info["pieces"][0]["piece_word"], 0x0000)
        self.assertEqual(info["pieces"][0]["raw_x"], 15)
        self.assertEqual(info["pieces"][0]["raw_y"], 15)

    def test_visual_frame_compiler_roundtrip(self) -> None:
        rom = synthetic_visual_descriptor_rom()
        frame, public = compiler_frame(rom, VISUAL_DESCRIPTOR, 0x0002)
        self.assertEqual(public["record_offset"], 0x0100)
        self.assertEqual(public["piece_count"], 1)
        self.assertEqual(public["dimensions"], [16, 16])
        self.assertEqual(frame["control0"], 1)
        self.assertEqual(frame["control1"], 2)
        self.assertEqual(frame["control2"], 3)
        self.assertEqual(frame["origin_x"], 100)
        self.assertEqual(frame["origin_y"], 200)

        records, chunks, metadata = compile_sequence([frame], group=0)
        self.assertEqual(metadata["frame_count"], 1)
        self.assertEqual(metadata["global_unique_chunks"], 1)
        self.assertEqual(len(chunks), 128)
        self.assertEqual(records[0][0x0F], 1)

        rebuilt = reconstruct_compiled(records[0], chunks, frame["image"].size)
        self.assertEqual(rebuilt.tobytes(), frame["image"].tobytes())
        self.assertEqual(
            records[0][:0x0F],
            bytes.fromhex("000100020003006400c80010001040"),
        )

    def test_non_grid_mapping_coordinate_is_rejected(self) -> None:
        rom = bytearray(synthetic_visual_descriptor_rom())
        record = VISUAL_DESCRIPTOR + 0x0100
        rom[record + 0x10] = 14
        with self.assertRaises(ValueError):
            compiler_frame(bytes(rom), VISUAL_DESCRIPTOR, 0x0002)


if __name__ == "__main__":
    unittest.main()
