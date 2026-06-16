from study.services.scoring import participant_score, average_understanding


def test_participant_score_correct_understood():
    # 이해(100)*0.7 + correct(100)*0.3 = 100
    assert participant_score("이해", True) == 100


def test_participant_score_unknown_wrong():
    # 모름(0)*0.7 + 0*0.3 = 0
    assert participant_score("모름", False) == 0


def test_participant_score_ambiguous_correct():
    # 애매(50)*0.7 + 100*0.3 = 65
    assert participant_score("애매", True) == 65


def test_participant_score_understood_wrong():
    # 이해(100)*0.7 + 0*0.3 = 70
    assert participant_score("이해", False) == 70


def test_average_understanding_rounds():
    assert average_understanding([100, 0]) == 50
    assert average_understanding([]) == 0


def test_unknown_understanding_defaults_to_zero_base():
    # unmapped string falls back to base 0; correct adds 30
    assert participant_score("???", True) == 30
