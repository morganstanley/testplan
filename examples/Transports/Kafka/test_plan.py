#!/usr/bin/env python
"""
Demostrates Kafka driver usage from within the testcases.
"""

import os
import sys
import uuid

from testplan import test_plan
from testplan.testing.multitest import MultiTest

try:
    from confluent_kafka import Producer, Consumer
except ImportError:
    print("Cannot import confluent_kafka!")
    sys.exit()

from testplan.testing.multitest.driver.zookeeper import (
    ZookeeperStandalone,
    ZK_SERVER,
)
from testplan.testing.multitest.driver.kafka import (
    KafkaStandalone,
    KAFKA_START,
)
from testplan.testing.multitest import testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


@testsuite
class KafkaTest(object):
    """Suite that contains testcases that perform kafka operation."""

    @testcase
    def test_send_receive(self, env, result):
        producer = Producer(
            {
                "bootstrap.servers": "localhost:{}".format(env.kafka.port),
                "max.in.flight": 1,
            }
        )
        consumer = Consumer(
            {
                "bootstrap.servers": "localhost:{}".format(env.kafka.port),
                "group.id": uuid.uuid4(),
                "default.topic.config": {"auto.offset.reset": "smallest"},
                "enable.auto.commit": True,
            }
        )

        topic = "testplan"
        message = str(uuid.uuid4()).encode("utf-8")
        producer.produce(topic=topic, value=message)
        producer.flush(10)
        consumer.subscribe([topic])
        msg = consumer.poll(10)
        result.equal(message, msg.value(), "Test producer and consumer")


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="KafkaExample",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
    pdf_path="report.pdf",
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    zookeeper_template = os.path.join(current_path, "zoo_template.cfg")
    kafka_template = os.path.join(current_path, "server_template.properties")

    plan.add(
        MultiTest(
            name="KafkaTest",
            suites=[KafkaTest()],
            environment=[
                ZookeeperStandalone(
                    name="zk", cfg_template=zookeeper_template
                ),
                KafkaStandalone(name="kafka", cfg_template=kafka_template),
            ],
        )
    )


if __name__ == "__main__":
    if os.path.exists(ZK_SERVER) and os.path.exists(KAFKA_START):
        sys.exit(not main())
    else:
        print("Zookeeper doesn't exist in this server.")
