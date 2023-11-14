from testplan.testing.multitest import testsuite, testcase


@testsuite
class TestOneClient:
    def setup(self, env, result):
        result.log(f"Testing with [{env.env_name}] env")
        env.server1.accept_connection()

    @testcase
    def test_send_and_receive_msg(self, env, result):
        env.client1.send_text("hi server")
        result.equal("hi server", env.server1.receive_text())

        env.server1.send_text("hi client")
        result.equal("hi client", env.client1.receive_text())


@testsuite
class TestTwoClients:
    def setup(self, env, result):
        result.log(f"Testing with [{env.env_name}] env")

        env.client1.connect()
        self.conn1 = env.server1.accept_connection()

        env.client2.connect()
        self.conn2 = env.server1.accept_connection()

    @testcase
    def test_send_and_receive_msg(self, env, result):
        env.client1.send_text("hi server from client1")
        env.client2.send_text("hi server from client2")

        result.equal(
            "hi server from client1",
            env.server1.receive_text(conn_idx=self.conn1),
        )
        result.equal(
            "hi server from client2",
            env.server1.receive_text(conn_idx=self.conn2),
        )

        env.server1.send_text("hi client1", conn_idx=self.conn1)
        env.server1.send_text("hi client2", conn_idx=self.conn2)

        result.equal("hi client1", env.client1.receive_text())
        result.equal("hi client2", env.client2.receive_text())
