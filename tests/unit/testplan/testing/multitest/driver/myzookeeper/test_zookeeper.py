"""Unit tests for the Zookeeper drivers."""

import os
import uuid
import pytest

from testplan.testing.multitest.driver import zookeeper

pytest.importorskip("kazoo")

from kazoo.client import KazooClient

pytestmark = pytest.mark.skipif(
    not os.path.exists(zookeeper.ZK_SERVER),
    reason="Zookeeper doesn't exist in this server.",
)

cfg_template = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "zoo_template.cfg"
)


@pytest.fixture(scope="module")
def zookeeper_server():
    server = zookeeper.ZookeeperStandalone(
        "zookeeper", cfg_template=cfg_template
    )
    with server:
        yield server


def test_zookeeper(zookeeper_server):
    test_value = str(uuid.uuid4()).encode("utf-8")

    zk_client1 = KazooClient(
        hosts="127.0.0.1:{}".format(zookeeper_server.port)
    )
    zk_client2 = KazooClient(
        hosts="127.0.0.1:{}".format(zookeeper_server.port)
    )
    zk_client1.start()
    zk_client2.start()

    zk_client1.ensure_path("/my")
    assert zk_client1.exists("/you") is None
    assert zk_client2.exists("/you") is None
    assert zk_client1.exists("/my") is not None
    assert zk_client2.exists("/my") is not None

    zk_client1.create("/my/testplan", test_value)
    data, _ = zk_client1.get("/my/testplan")
    assert data == test_value
    data, _ = zk_client2.get("/my/testplan")
    assert data == test_value

    zk_client2.set("/my/testplan", str(uuid.uuid4()).encode("utf-8"))
    data, _ = zk_client1.get("/my/testplan")
    assert data != test_value
    data, _ = zk_client2.get("/my/testplan")
    assert data != test_value
