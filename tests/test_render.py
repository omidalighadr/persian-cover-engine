import hashlib
import itertools

import pytest
from PIL import ImageChops

from persian_cover import SIZES, CoverSpec, plan, render, render_bytes
from persian_cover.layout import contains

TITLES = [
    "سلام",
    "چطور با هوش مصنوعی مقاله بنویسیم؟",
    "راهنمای کامل انتخاب موضوع پایان‌نامه برای دانشجویان تحصیلات تکمیلی در سال ۱۴۰۵",
    "Designing reliable queues for background workers",
    "ترکیب Python و دواپس: 7 اشتباه رایج",
]


@pytest.mark.parametrize(("title", "size"), list(itertools.product(TITLES, sorted(SIZES))))
def test_all_text_stays_inside_the_grid_safe_box(title, size):
    lay = plan(
        CoverSpec(title=title, subtitle="زیرعنوان نمونه برای آزمایش", handle="@example", size=size)
    )
    lines = [*lay.title, *lay.subtitle, *([lay.handle] if lay.handle else [])]
    assert lines
    for ln in lines:
        assert contains(lay.safe, ln.box), (ln.text, ln.box, lay.safe)


def test_title_block_is_inside_safe_box_even_for_a_huge_title():
    lay = plan(CoverSpec(title=" ".join(["کلمه"] * 300), size="story"))
    assert all(contains(lay.safe, ln.box) for ln in lay.title)
    assert len(lay.title) <= 5


def test_render_has_requested_size_and_mode():
    im = render(CoverSpec(title="سلام دنیا", size="square"))
    assert im.size == SIZES["square"] and im.mode == "RGB"


def test_render_is_deterministic():
    spec = CoverSpec(
        title="چطور با هوش مصنوعی مقاله بنویسیم؟", highlight="هوش", subtitle="۱۰ دقیقه"
    )
    assert render_bytes(spec) == render_bytes(spec)


def test_highlight_changes_the_pixels():
    a = render(CoverSpec(title="چطور با هوش مصنوعی مقاله بنویسیم؟"))
    b = render(CoverSpec(title="چطور با هوش مصنوعی مقاله بنویسیم؟", highlight="هوش"))
    assert ImageChops.difference(a, b).getbbox() is not None


def test_background_styles_differ():
    r = render(CoverSpec(title="سلام", background="radial"))
    li = render(CoverSpec(title="سلام", background="linear"))
    assert ImageChops.difference(r, li).getbbox() is not None


def test_text_actually_drawn_inside_safe_box_only():
    # same cover with and without text: every differing pixel must lie inside the safe box
    spec = CoverSpec(
        title="چطور با هوش مصنوعی مقاله بنویسیم؟",
        subtitle="زیرعنوان",
        handle="@example",
        size="story",
    )
    full = render(spec)
    empty = render(CoverSpec(title="x", size="story"))  # same background, tiny title
    diff = ImageChops.difference(full, empty).getbbox()
    lay = plan(spec)
    assert diff is not None and contains(lay.safe, diff)


@pytest.mark.parametrize("kwargs", [{"size": "nope"}, {"palette": "nope"}, {"background": "nope"}])
def test_invalid_options_raise_clear_errors(kwargs):
    with pytest.raises(ValueError):
        render(CoverSpec(title="سلام", **kwargs))


def test_empty_title_is_rejected():
    with pytest.raises(ValueError, match="title"):
        render(CoverSpec(title="   "))


def test_reshaper_backend_renders_too(monkeypatch):
    pytest.importorskip("arabic_reshaper")
    pytest.importorskip("bidi")
    monkeypatch.setenv("PERSIAN_COVER_SHAPING", "reshaper")
    im = render(CoverSpec(title="سلام دنیا"))
    assert im.size == SIZES["post"]
    assert hashlib.sha1(im.tobytes()).hexdigest()  # rendered without raising
