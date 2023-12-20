from unittest.mock import patch


def test_empty_testplan(mockplan):
    with patch("logging.Logger.warning") as mock_logger:
        result = mockplan.run()
        mock_logger.assert_called_with("Empty report, nothing to be exported!")
    report = result.report
    assert report.is_empty() is True
