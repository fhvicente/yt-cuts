def test_package_imports():
    import yt_cuts  # noqa: F401


def test_sample_video_fixture(sample_video):
    assert sample_video.exists()
    assert sample_video.suffix == ".mp4"
