import logging


def test_logging_disabled_by_default(unit_test_logging):
    logging_instance, logger, log_exporter = unit_test_logging
    assert logging_instance._logging_enabled is False
    logger.log(msg="no_op_log_message", level=logging.INFO)
    log_records = log_exporter.get_finished_logs()
    assert len(log_records) == 0


def test_basic_log(unit_test_logging):
    logging_instance, logger, log_exporter = unit_test_logging
    logging_instance._setup()

    message = "hello test log"
    logger.info(message)
    log_records = log_exporter.get_finished_logs()
    assert len(log_records) == 1
    record = log_records[0]
    actual_message = record.log_record.body
    assert actual_message == message
