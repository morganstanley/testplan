"""Unit tests for the Zookeeper drivers."""

from pytest_test_filters import skip_module_on_windows

skip_module_on_windows("Kafka not available on windows")


import os
import uuid
import pytest

from testplan.common import entity
from testplan.base import TestplanMock
from testplan.testing.multitest.driver import kafka

pytest.importorskip("confluent_kafka")
from confluent_kafka import Producer, Consumer

pytestmark = pytest.mark.skipif(
    not os.path.exists(kafka.KAFKA_START),
    reason="Kafka doesn't exist in this server.",
)

kafka_cfg_template = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "server_template.properties"
)


@pytest.fixture(scope="module")
def kafka_server(runpath_module):
    server = kafka.KafkaStandalone(
        "kafka",
        cfg_template=kafka_cfg_template,
        runpath=runpath_module,
        host="localhost",
    )

    testplan = TestplanMock("KafkaTest", parse_cmdline=False)
    env = entity.Environment(parent=testplan)
    env.add(server)

    with server:
        yield server


def test_kafka(kafka_server):
    producer = Producer(
        {
            "bootstrap.servers": f"localhost:{kafka_server.port}",
            "max.in.flight": 1,
            "client.id": "kafka-client",
            "acks": 1,  # Wait for leader acknowledgment only
            "request.timeout.ms": 30000,  # Add timeout
            "delivery.timeout.ms": 30000,  # Add delivery timeout
        }
    )
    consumer = Consumer(
        {
            "bootstrap.servers": f"localhost:{kafka_server.port}",
            "group.id": uuid.uuid4(),
            "default.topic.config": {"auto.offset.reset": "smallest"},
            "enable.auto.commit": True,
            "broker.address.family": "v4",
        }
    )

    topic = "testplan"
    message = str(uuid.uuid4()).encode("utf-8")
    producer.produce(topic=topic, value=message)
    consumer.subscribe([topic])
    msg = consumer.poll(10)
    assert message == msg.value()
