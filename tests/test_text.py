import pytest

from persian_cover import text as t


def test_is_rtl():
    assert t.is_rtl("سلام")
    assert not t.is_rtl("hello 123")


def test_digits_are_localised_only_in_persian_text():
    assert t.localize_digits("۱۰ روز 10") == "۱۰ روز ۱۰"
    assert t.localize_digits("Top 10 tools") == "Top 10 tools"


def test_wrap_respects_width_and_keeps_every_word():
    font = t.load_font(60, bold=True)
    words = [
        "چطور",
        "با",
        "هوش",
        "مصنوعی",
        "مقاله",
        "بنویسیم",
        "و",
        "منبع‌ها",
        "را",
        "درست",
        "بیاوریم",
    ]
    lines = t.wrap(" ".join(words), font, max_width=500)
    assert len(lines) > 1
    assert " ".join(lines).split() == words
    assert all(t.measure(font, ln) <= 500 for ln in lines)


def test_wrap_keeps_explicit_newlines():
    font = t.load_font(40)
    assert t.wrap("اول\nدوم", font, 10_000) == ["اول", "دوم"]


def test_fit_picks_the_largest_size_that_fits():
    make = lambda s: t.load_font(s, bold=True)  # noqa: E731
    big = t.fit("سلام", make, max_width=900, max_height=400, top=200, low=40, max_lines=3)
    assert big.size == 200
    long = "این یک عنوان بسیار طولانی برای آزمایش کوچک شدن اندازه فونت است"
    small = t.fit(long, make, max_width=600, max_height=500, top=200, low=40, max_lines=5)
    assert small.size < 200
    assert len(small.lines) <= 5
    assert len(small.lines) * small.line_height <= 500


def test_fit_truncates_instead_of_overflowing():
    make = lambda s: t.load_font(s)  # noqa: E731
    long = " ".join(["کلمه"] * 200)
    r = t.fit(long, make, max_width=400, max_height=300, top=80, low=40, max_lines=3)
    assert r.size == 40 and len(r.lines) <= 3


def test_backend_override(monkeypatch):
    monkeypatch.setenv("PERSIAN_COVER_SHAPING", "reshaper")
    assert t.shaping_backend() == "reshaper"
    monkeypatch.setenv("PERSIAN_COVER_SHAPING", "raqm")
    assert t.shaping_backend() == "raqm"


def test_reshaper_backend_produces_presentation_forms(monkeypatch):
    pytest.importorskip("arabic_reshaper")
    pytest.importorskip("bidi")
    monkeypatch.setenv("PERSIAN_COVER_SHAPING", "reshaper")
    shaped = t.prepare("سلام")
    assert shaped != "سلام" and any("ﭐ" <= c <= "ﻼ" for c in shaped)
