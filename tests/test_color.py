import pytest

from persian_cover.color import PALETTES, Palette, contrast_ratio, mix, parse_hex


def test_black_on_white_is_21():
    assert contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)


def test_identical_colours_are_1():
    assert contrast_ratio((10, 20, 30), (10, 20, 30)) == pytest.approx(1.0)


def test_parse_hex_accepts_optional_hash():
    assert parse_hex("#0f172a") == parse_hex("0F172A") == (15, 23, 42)


@pytest.mark.parametrize("bad", ["", "#fff", "#12345g", "1234567"])
def test_parse_hex_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        parse_hex(bad)


def test_mix_endpoints():
    assert mix((0, 0, 0), (200, 100, 50), 0) == (0, 0, 0)
    assert mix((0, 0, 0), (200, 100, 50), 1) == (200, 100, 50)


@pytest.mark.parametrize("name", sorted(PALETTES))
def test_builtin_palettes_meet_wcag_aa(name):
    PALETTES[name].validate()  # raises if text < 4.5, subtitle < 4.5 or accent < 3


def test_validate_rejects_low_contrast_palette():
    bad = Palette("bad", edge="#777777", center="#888888", accent="#999999", text="#aaaaaa")
    with pytest.raises(ValueError, match="contrast"):
        bad.validate()
