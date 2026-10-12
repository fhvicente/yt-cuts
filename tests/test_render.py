from yt_cuts.ffmpeg_utils import probe_dimensions
from yt_cuts.models import Segment
from yt_cuts.reframe.static_center import StaticCenterReframer
from yt_cuts.render import render_clip


def test_render_produces_vertical_clip(sample_video, tmp_path):
    ass = tmp_path / "clip.ass"
    ass.write_text(
        "[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        "Style: Karaoke,Arial,72,&H0000FFFF,&H00FFFFFF,&H00000000,&H64000000,"
        "-1,0,0,0,100,100,0,0,1,4,1,2,60,60,240,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:00.00,0:00:01.00,Karaoke,,0,0,0,,{\\kf100}olá\n"
    )
    out = tmp_path / "clip_00.mp4"
    result = render_clip(
        sample_video, Segment(0.0, 1.0), ass, out, StaticCenterReframer(), (1280, 720)
    )
    assert out.exists()
    assert result.width == 1080 and result.height == 1920
    assert probe_dimensions(out) == (1080, 1920)
