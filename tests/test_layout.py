import pytest

from persian_cover.layout import SIZES, contains, grid_frame


def test_grid_frame_for_story_is_centre_3_4_crop():
    # 1080x1920: crop height = 1080*4/3 = 1440, so y in [240, 1680]
    assert grid_frame(1080, 1920) == (0, 240, 1080, 1680)


def test_grid_frame_for_4_5_post_crops_the_sides():
    x0, y0, x1, y1 = grid_frame(1080, 1350)
    assert (y0, y1) == (0, 1350)
    assert (x1 - x0) * 4 == 1350 * 3 or abs((x1 - x0) * 4 - 1350 * 3) < 4
    assert x0 == 1080 - x1  # centred


def test_grid_frame_landscape_is_not_cropped():
    assert grid_frame(1920, 1080) == (0, 0, 1920, 1080)


@pytest.mark.parametrize("size", sorted(SIZES))
def test_frame_is_inside_canvas_and_centred(size):
    w, h = SIZES[size]
    box = grid_frame(w, h)
    assert contains((0, 0, w, h), box)
    assert abs((box[0] + box[2]) - w) <= 1 and abs((box[1] + box[3]) - h) <= 1
