import numpy as np
import pytest

from organoid_anticipation.io.d001611 import infer_time_scale


def test_time_scale_ms():
    assert infer_time_scale(np.arange(0, 256) * 1000.0 + 3192.3) == (1e-3, "ms")


def test_time_scale_s():
    assert infer_time_scale(np.arange(0, 256) * 1.0) == (1.0, "s")


def test_time_scale_bad():
    with pytest.raises(ValueError):
        infer_time_scale(np.arange(0, 256) * 30.0)
