package testplan;

import testplan.environment.drivers.Driver;
import testplan.environment.drivers.DriverEntry;
import testplan.environment.Environment;

import java.util.HashMap;
import java.util.LinkedList;


/**
 * Main class to demonstrate Testplan interactive usage in java.
 */
public class Main {

    /**
     * Create a TCPServer entry to be added in the environment.
     *
     * @param name Name of the TCPServer.
     * @return     A TCPServer - DriverEntry containing the python driver
     *             initialisation parameters.
     */
    public static DriverEntry getTCPServer(final String name){
        HashMap<String, Object> serverArgs = new HashMap<String, Object>(){{
            this.put("name", name);
        }};
        return new DriverEntry("TCPServer", serverArgs);
    }

    /**
     * Create a TCPClient entry to be added in the environment.
     *
     * @param name       Name of the TCPClient.
     * @param serverName Name of server to connect to.
     * @return           A TCPServer - DriverEntry containing the python driver
     *                   initialisation parameters. The special _ctx_ABC_ctx_XYZ
     *                   values will be translated by Testplan interactive into
     *                   a context object.
     */
    public static DriverEntry getTCPClient(final String name, final String serverName){
        // This demonstrates context() utility usage via HTTP.
        HashMap<String, Object> clientArgs = new HashMap<String, Object>(){{
           this.put("name", name);
           this.put("_ctx_host_ctx_driver", serverName);
           this.put("_ctx_host_ctx_value", "{{host}}");
           this.put("_ctx_port_ctx_driver", serverName);
           this.put("_ctx_port_ctx_value", "{{port}}");
        }};
        return new DriverEntry("TCPClient", clientArgs);
    }

    /**
     * Creates an environment instance.
     *
     * @param envUid Uid for the environment to be added.
     * @return       An environment containing driver entries that will be added
     *               to Testplan interactive process.
     */
    public static Environment getEnvironment(String envUid) {
        LinkedList<DriverEntry> driverEntries = new LinkedList<DriverEntry>();
        driverEntries.addLast(getTCPServer("server"));
        driverEntries.addLast(getTCPClient("client", "server"));
        Environment env = new Environment(envUid, driverEntries);
        return env;
    }

    /**
     * Demonstrates Testplan interactive usage of environment in java.
     */
    public static void main(String[] args) throws Exception{
        // Initialise a Testplan interactive instance.

        // Test Testplan scipt can be an empty Testplan executable
        // that will be started with the specified interpreter
        // with --interactive parameter.
        TestplanInteractive plan = new TestplanInteractive(
                "<PATH_TO_PYTHON_INTERPRETER>",
                "<PATH_TO_PYTHON_TESTPLAN_SCRIPT>");


        // Start Testplan interactive mode.
        plan.startInteractive();

        // Add and start and environment with a local TCP server and client.
        plan.addAndStartEnvironment(getEnvironment("myEnv"));

        Driver server = plan.getDriver("myEnv", "server");
        Driver client = plan.getDriver("myEnv", "client");

        // Server accepts connection.
        server.method("accept_connection").exec();

        // Client sends text message.
        client.method("send_text").kwarg("msg", "Hello world!").exec();

        // Server receives the message!
        String received = (String) server.method("receive_text").exec();
        System.out.println("Received from server: " + received);

        // Stop Testplan instance.
        plan.stopInteractive();
    }
}
