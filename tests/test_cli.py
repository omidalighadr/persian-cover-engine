from PIL import Image

from persian_cover.cli import main


def test_cli_renders_file(tmp_path, capsys):
    out = tmp_path / "c.png"
    assert main(["سلام دنیا", "--size", "square", "--palette", "ivory", "--out", str(out)]) == 0
    assert Image.open(out).size == (1080, 1080)
    assert "1080x1080" in capsys.readouterr().out


def test_cli_contrast_report(capsys):
    assert main(["--contrast-report"]) == 0
    out = capsys.readouterr().out
    assert "teal" in out and "ivory" in out


def test_cli_spec_file(tmp_path):
    spec = tmp_path / "s.json"
    spec.write_text('{"title": "Hello", "size": "wide", "palette": "midnight"}', encoding="utf-8")
    out = tmp_path / "o.png"
    assert main(["--spec", str(spec), "--out", str(out)]) == 0
    assert Image.open(out).size == (1920, 1080)


def test_cli_reports_bad_palette_without_traceback(tmp_path):
    spec = tmp_path / "s.json"
    spec.write_text('{"title": "x", "palette": "nope"}', encoding="utf-8")
    assert main(["--spec", str(spec), "--out", str(tmp_path / "o.png")]) == 2
