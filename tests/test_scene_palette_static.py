from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
from scene_palette import CRAM_MASK, PALETTE_WORDS, align, validate_colors


def test_valid_cram_words_are_accepted() -> None:
    colors = [0x0000] * PALETTE_WORDS
    colors[1] = 0x0002
    colors[2] = 0x0020
    colors[3] = 0x0200
    colors[4] = 0x0EEE
    assert validate_colors(colors) == colors
    assert all((value & ~CRAM_MASK) == 0 for value in colors)


def test_invalid_cram_low_bit_is_rejected() -> None:
    colors = [0x0000] * PALETTE_WORDS
    colors[7] = 0x0001
    with pytest.raises(ValueError):
        validate_colors(colors)


def test_invalid_cram_high_bit_is_rejected() -> None:
    colors = [0x0000] * PALETTE_WORDS
    colors[9] = 0x1000
    with pytest.raises(ValueError):
        validate_colors(colors)


def test_palette_length_is_exact() -> None:
    with pytest.raises(ValueError):
        validate_colors([0x0000] * (PALETTE_WORDS - 1))
    with pytest.raises(ValueError):
        validate_colors([0x0000] * (PALETTE_WORDS + 1))


def test_non_integer_color_is_rejected() -> None:
    colors = [0x0000] * PALETTE_WORDS
    colors[0] = "0x0000"  # type: ignore[list-item]
    with pytest.raises(TypeError):
        validate_colors(colors)  # type: ignore[arg-type]


def test_alignment_contract() -> None:
    assert align(0x300000) == 0x300000
    assert align(0x300001) == 0x300010
    assert align(0x300010) == 0x300010
