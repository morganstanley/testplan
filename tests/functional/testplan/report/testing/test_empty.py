from unittest.mock import patch


def test_empty_testplan(mockplan):
    with patch("logging.Logger.warning") as mock_logger:
        result = mockplan.run()
        mock_logger.assert_any_call("No tests were added, skipping execution!")
    report = result.report
    assert result.run is True
    assert result.exit_code == 0
    assert report.is_empty() is True
