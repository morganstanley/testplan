from testplan.testing.multitest.entries import base

from testplan.testing.multitest.entries import assertions


def test_double_summary_prevention():
    """
    Summary.summarize should flatten Group.entries
    and include other Summary entries directly.
    """

    asr_1 = assertions.Equal(1, 1)
    asr_2 = assertions.Equal(2, 2)
    asr_3 = base.Group(
        entries=[
            assertions.Equal(3, 3),
            assertions.Equal(3, 3)
        ]
    )
    asr_4 = base.Summary(
        entries=[
            assertions.IsTrue(True),
            assertions.Greater(3, 2)
        ]
    )
    asr_5 = assertions.Equal(3, 3)

    summary = base.Summary(
        entries=[
            asr_1,
            asr_2,
            asr_3,
            asr_4,
            asr_5
        ],
        num_passing=5,
    )

    assert len(summary.entries) == 2

    existing_summary, category_group = summary.entries

    assert isinstance(category_group, base.Group)
    assert existing_summary == asr_4


def test_summary():
    """
    Summary.summarize should group entries by
    category, entry class and pass status,
    leaving out non-assertion entries.
    """

    asr_1 = assertions.Equal(1, 1)
    asr_2 = assertions.Equal(1, 1, category='alpha')
    asr_3 = assertions.Less(1, 2)
    asr_4 = assertions.Less(3, 4, category='alpha')
    asr_5 = assertions.Equal(1, 2)
    asr_6 = assertions.Less(4, 4, category='alpha')
    less_failing = [
        assertions.Less(4, 4, category='alpha') for _ in range(100)
        ]
    less_passing = [
        assertions.Less(3, 4, category='alpha') for _ in range(100)
        ]

    summary = base.Summary(
        entries=[
            asr_1, asr_2, base.Log('foo'),
            asr_3, asr_4, base.Log('bar'), asr_5, asr_6
        ] + less_failing + less_passing,
        num_passing=3,
        num_failing=4,
    )

    no_category, alpha_category = summary.entries

    # Top level groups
    assert isinstance(no_category, base.Group)
    assert isinstance(alpha_category, base.Group)

    no_category_equal, no_category_less = no_category.entries

    # Assertion type groups for no category
    assert isinstance(no_category_equal, base.Group)
    assert isinstance(no_category_less, base.Group)

    entries = no_category_equal.entries
    no_category_equal_failing, no_category_equal_passing = entries

    # pass/fail groups for equal assertion
    assert isinstance(no_category_equal_passing, base.Group)
    assert isinstance(no_category_equal_failing, base.Group)

    assert no_category_equal_passing.entries == [asr_1]
    assert no_category_equal_failing.entries == [asr_5]

    # No failing Less assertion for None category
    assert len(no_category_less.entries) == 1
    no_category_less_passing = no_category_less.entries[0]

    assert no_category_less_passing.entries == [asr_3]

    alpha_category_equal, alpha_category_less = alpha_category.entries

    assert isinstance(alpha_category_equal, base.Group)
    assert isinstance(alpha_category_less, base.Group)

    # No failing Equal assertion for alpha category
    assert len(alpha_category_equal.entries) == 1

    alpha_category_equal_passing = alpha_category_equal.entries[0]
    assert isinstance(alpha_category_equal_passing, base.Group)
    assert alpha_category_equal_passing.entries == [asr_2]

    entries = alpha_category_less.entries
    alpha_category_less_failing, alpha_category_less_passing = entries

    assert isinstance(alpha_category_less_passing, base.Group)
    assert isinstance(alpha_category_less_failing, base.Group)

    assert len(alpha_category_less_passing.entries) == summary.num_passing
    assert len(alpha_category_less_failing.entries) == summary.num_failing


