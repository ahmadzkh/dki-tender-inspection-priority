def test_project_package_importable() -> None:
    from procurement_priority import __version__

    assert __version__ == "0.1.0"
