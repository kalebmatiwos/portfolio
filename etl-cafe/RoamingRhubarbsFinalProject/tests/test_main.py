def test_main_imports_pipeline_modules():
    import main

    assert callable(main.main)
