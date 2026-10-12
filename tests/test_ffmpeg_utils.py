import pytest

from yt_cuts.ffmpeg_utils import FFmpegError, probe_dimensions, run


def test_probe_dimensions_on_sample(sample_video):
    assert probe_dimensions(sample_video) == (1280, 720)


def test_run_raises_on_bad_args():
    with pytest.raises(FFmpegError):
        run(["-i", "/does/not/exist/file.mp4", "/tmp/out_zzz.mp4"])
