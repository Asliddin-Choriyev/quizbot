from bot.utils.i18n import t

def test_i18n_translation():
    # Test Uzbek default
    uz_welcome = t("welcome_title", "uz")
    assert "xush kelibsiz" in uz_welcome

    # Test English
    en_welcome = t("welcome_title", "en")
    assert "Welcome" in en_welcome

    # Test fallback on unknown language
    fallback = t("welcome_title", "fr")
    assert "xush kelibsiz" in fallback or "Welcome" in fallback

    # Test parameter formatting
    res = t("quiz_landing", "en", title="Sample Quiz", description="Desc", question_count=10, timer=30)
    assert "Sample Quiz" in res
    assert "10 questions" in res
    assert "30 seconds" in res
