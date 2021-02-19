/**
 * JUnit for the example JavaCode class.
 * This file demonstrates usage of a python Testplan environment
 * from within a java testing framework.
 */

import org.junit.After;
import org.junit.Assert;
import org.junit.Before;

import org.junit.Test;

import java.util.LinkedList;
import java.util.HashMap;

import testplan.TestplanInteractive;
import testplan.environment.Environment;
import testplan.environment.drivers.Driver;
import testplan.environment.drivers.DriverEntry;


public class JavaCodeTest {
    TestplanInteractive plan;

    /**
     * Create a new environment with a TCP server and a client connecting
     * to the server using the context mechanism.
     *
     * @param envUid Uid of the new environment.
     * @return       Environment to be added to Testplan.
     */
    Environment createEnv(String envUid){
        LinkedList<DriverEntry> myEnvDriverEntries = new LinkedList<DriverEntry>();
        // Add a server.
        myEnvDriverEntries.addLast(
                new DriverEntry(
                        "TCPServer",
                        new HashMap<String, Object>(){{
                            this.put("name", "server");
                        }})
        );
        // Add a client.
        myEnvDriverEntries.addLast(
                new DriverEntry(
                        "TCPClient",
                        new HashMap<String, Object>(){{
                            this.put("name", "client");
                            this.put("_ctx_host_ctx_driver", "server");
                            this.put("_ctx_host_ctx_value", "{{host}}");
                            this.put("_ctx_port_ctx_driver", "server");
                            this.put("_ctx_port_ctx_value", "{{port}}");
                        }})
        );
        return new Environment(envUid, myEnvDriverEntries);
    }

    /**
     * Setup method that we create and start a Testplan background instance
     * process be used (via HTTP) by the tests that may need access to the
     * environment drivers.
     */
    @Before
    public void setUp() throws Exception {
        plan = new TestplanInteractive(
                "<PATH_TO_PYTHON_INTERPRETER>",
                "<PATH_TO_PYTHON_TESTPLAN_SCRIPT>");

        // Start Testplan interactive mode.
        plan.startInteractive();

        // Add and start and environment with a local TCP server and client.
        plan.addAndStartEnvironment(createEnv("myEnv"));
    }

    /**
     * Example testcase that demonstrates access to Testplan live environment
     * and drivers methods usage.
     */
    @Test
    public void testCode() throws Exception{
        JavaCode jcode = new JavaCode();

        Driver server = this.plan.getDriver("myEnv", "server");
        Driver client = this.plan.getDriver("myEnv", "client");

        // Server accepts connection.
        server.method("accept_connection").exec();

        // Client sends text message.
        client.method("send_text").kwarg("msg", "Hello Server!").exec();

        // Server receives the message!
        String received = (String) server.method("receive_text").exec();
        System.out.println("Server received message: " + received);

        // Assert code functionality.
        Assert.assertEquals(jcode.toLower(received), "hello server!");
        Assert.assertEquals(jcode.toUpper(received), "HELLO SERVER!");
    }

    /**
     * Teardown method that stops the environment and destroys the background
     * Testplan instance.
     */
    @After
    public void tearDown() throws Exception {
        plan.stopInteractive();
    }
}
