from matrix_maintainer.site.generator import generate_site


def test_legacy_site_generator_shim_importable():
    assert callable(generate_site)
