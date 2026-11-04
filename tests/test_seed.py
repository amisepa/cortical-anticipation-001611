from organoid_anticipation import derive_seed


def test_derive_seed_deterministic():
    assert derive_seed("a") == derive_seed("a")
    assert derive_seed("a") != derive_seed("b")
