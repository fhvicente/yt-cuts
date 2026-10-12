from yt_cuts.reframe.base import get_reframer
from yt_cuts.reframe.static_center import StaticCenterReframer


def test_static_crop_filter_from_16x9():
    f = StaticCenterReframer().crop_filter(1920, 1080)
    # 9:16 de 1080 alto => largura 608 (par), centrado em x=656, scale final 1080x1920
    assert f == "crop=608:1080:656:0,scale=1080:1920"


def test_crop_dims_are_even():
    f = StaticCenterReframer().crop_filter(1281, 721)
    crop = f.split(",")[0]  # crop=W:H:X:Y
    _, dims = crop.split("=")
    w, h, _x, _y = (int(v) for v in dims.split(":"))
    assert w % 2 == 0 and h % 2 == 0


def test_registry_returns_static():
    assert isinstance(get_reframer("static"), StaticCenterReframer)
