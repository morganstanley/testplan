"""Tests TCP communication among multiple servers and multiple clients."""

from testplan.testing.multitest import testsuite, testcase


@testsuite
class MultiTCPSuite:
    """TCP tests for multiple servers and multiple clients."""

    @testcase
    def test_send_and_receive_msg(self, env, result):
        """
        Client sends a message, server received and responds back.
        """
        env.client_1.send_text("zhengshan xiaozhong")
        env.server_1.accept_connection()
        result.equal("zhengshan xiaozhong", env.server_1.receive_text())
        env.server_1.send_text("good black tea")
        result.equal("good black tea", env.client_1.receive_text())

        env.client_2.send_text("whisky")
        conn_2 = env.server_2.accept_connection()
        env.client_3.send_text("soda water")
        conn_3 = env.server_2.accept_connection()
        result.equal("whisky", env.server_2.receive_text(conn_idx=conn_2))
        result.equal("soda water", env.server_2.receive_text(conn_idx=conn_3))
        env.server_2.send_text("good highball", conn_idx=conn_2)
        env.server_2.send_text("good highball", conn_idx=conn_3)
        result.equal("good highball", env.client_2.receive_text())
        result.equal("good highball", env.client_3.receive_text())
