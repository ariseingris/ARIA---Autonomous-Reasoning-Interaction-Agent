from aria.config import Settings


def test_settings_loads_env_file_and_toml(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ARIA_MODEL", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "aria.toml").write_text(
        """
        [aria]
        model = "from-toml"
        memory_backend = "chroma"
        data_dir = ".data"
        """,
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        """
        OPENAI_API_KEY=env-file-key
        ARIA_MODEL=from-env-file
        """,
        encoding="utf-8",
    )

    settings = Settings.load(tmp_path)

    assert settings.openai_api_key == "env-file-key"
    assert settings.model == "from-env-file"
    assert settings.memory_backend == "chroma"
    assert settings.data_dir.name == ".data"


def test_real_environment_overrides_env_file(tmp_path, monkeypatch):
    monkeypatch.setenv("ARIA_MODEL", "from-real-env")
    (tmp_path / ".env").write_text("ARIA_MODEL=from-env-file\n", encoding="utf-8")

    settings = Settings.load(tmp_path)

    assert settings.model == "from-real-env"
