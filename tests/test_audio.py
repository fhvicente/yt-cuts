from yt_cuts.audio import extract_audio


def test_extract_audio_creates_wav(sample_video, tmp_path):
    out = tmp_path / "audio.wav"
    result = extract_audio(sample_video, out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0
