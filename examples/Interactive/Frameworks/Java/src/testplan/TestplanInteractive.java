/**
 * Testplan package providing the classes to:
 *   1. Create a background python Testplan interactive process.
 *   2. Provide operations that are translating to HTTP requests to the
 *      background instance to manipulate Testplan environments.
 *   3. Access the environment drivers to perform actual operations.
 */
package testplan;

import testplan.environment.Environment;
import testplan.environment.drivers.Driver;
import testplan.environment.drivers.DriverEntry;

import java.io.*;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.regex.*;
import java.io.IOException;

/**
 * Testplan interactive main class.
 */
public class TestplanInteractive {
    TestplanThread planThread;
    String ip;
    String port;
    HashMap<String, Environment> envs;
    HttpRequests requests;


    /**
     * Constructor storing all information needed for starting
     * the background python process.
     *
     * @param interpreter  Path to local python interpreter.
     * @param testplanPath Path to a python Testplan file that can run with
     *                     the specified interpreter in interactive mode.
     */
    public TestplanInteractive(String interpreter, String testplanPath) {
        this.planThread = new TestplanThread(interpreter, testplanPath);
        this.envs = new HashMap<String, Environment>();
        this.requests = null;
    }

    /**
     * Start a background Testplan interactive instance and retrieve
     * the ip/port information for the HTTP listener.
     */
    public void startInteractive() throws InterruptedException {
        this.planThread.start();
        while (this.planThread.port == null) {
            Thread.sleep(500);
        }
        this.ip = planThread.ip;
        this.port = planThread.port;
        this.requests = new HttpRequests(this.ip, this.port);
        System.out.println("Testplan listening on: " + this.ip + ':' + this.port);
        return;
    }

    /**
     * Stop the environments and the background Testplan process.
     */
    public void stopInteractive() throws Exception {
        for (String envUid : this.envs.keySet()) {
            this.envStop(envUid);
        }
        this.planThread.doStop();
    }

    /**
     * Retrieve and perform the HTTP requests needed to add an
     * environment in the Testplan instance.
     *
     * @param env Environment object containing driver entries information
     *            to be translated into HTTP requests to the background instance.
     */
    public void addEnvironment(Environment env) throws Exception {
        System.out.println("Adding environment: " + env.getUid());
        for (DriverEntry driver : env.getDrivers()) {
            System.out.println("    with driver: " + driver.getArg("name"));
        }
        // Many HTTP requests are involved for the environment to be added.
        LinkedList<HashMap<String, Object>> postRequests = env.addEnvironmentRequests();
        for (HashMap<String, Object> data : postRequests) {
            String operation = (String) data.get("operation");
            data.remove("operation");
            HashMap<String, Object> response = this.requests.sendPost(
                    "/sync/" + operation, data);
        }
        this.envs.put(env.getUid(), env);
    }

    /**
     * Add the environment but also start it()
     * @param env Target environment.
     */
    public void addAndStartEnvironment(Environment env) throws Exception {
        this.addEnvironment(env);
        this.envStart(env.getUid());
    }


    /**
     * Driver context value retrieval.
     *
     * @param envUid       Environment uid containing the driver.
     * @param driverUid    Driver uid.
     * @param context_item Target context item for lookup.
     * @return             The context item value.
     */
    public Object getDriverContextValue(
            String envUid, String driverUid, String context_item) throws Exception {
        HashMap<String, Object> data = this.getEnvironment(envUid).getContextValueRequest(driverUid, context_item);
        String operation = (String) data.get("operation");
        data.remove("operation");
        HashMap<String, Object> response = this.requests.sendPost(
                "/sync/" + operation, data);
        return response.get("result");
    }

    /**
     * Add a driver in an environment.
     *
     * @param envUid Environment uid.
     * @param driver Driver to be added.
     */
    public void addDriver(String envUid, DriverEntry driver) throws Exception {
        HashMap<String, Object> data = this.getEnvironment(envUid).addDriverRequest(driver);
        String operation = (String) data.get("operation");
        data.remove("operation");
        HashMap<String, Object> response = this.requests.sendPost(
                "/sync/" + operation, data);
    }

    /**
     * Add a driver in an environment and start it.
     *
     * @param envUid Environment uid.
     * @param driverEntry Driver to be added and started.
     */
    public void addAndStartDriver(String envUid, DriverEntry driverEntry) throws Exception {
        this.addDriver(envUid, driverEntry);

        Driver driver = this.getDriver(envUid, driverEntry.getUid());
        driver.method("start").exec();
    }

    /**
     * Retrieves an environment from its uid.
     *
     * @param envUid Input uid.
     * @return       An environment object.
     */
    public Environment getEnvironment(String envUid) {
        return this.envs.get(envUid);
    }

    /**
     * Performs the HTTP request required to start an environment.
     * @param envUid Environment uid.
     */
    public void envStart(String envUid) throws Exception {
        System.out.println("Starting environment: " + envUid);
        Environment env = this.getEnvironment(envUid);
        HashMap<String, Object> data = env.startEnvironmentRequest();
        String operation = (String) data.get("operation");
        data.remove("operation");
        HashMap<String, Object> response = this.requests.sendPost(
                "/sync/" + operation, data);
    }

    /**
     * Performs the HTTP request required to stop an environment.
     * @param envUid Environment uid.
     */
    public void envStop(String envUid) throws Exception {
        System.out.println("Stopping environment: " + envUid);
        Environment env = this.getEnvironment(envUid);
        HashMap<String, Object> data = env.stopEnvironmentRequest();
        String operation = (String) data.get("operation");
        data.remove("operation");
        HashMap<String, Object> response = this.requests.sendPost(
                "/sync/" + operation, data);
    }

    /**
     * Create a driver object that can be used to perform actual
     * driver operations via HTTP requests.
     * @param envUid    Environment uid that contains the driver.
     * @param driverUid Target driver uid.
     * @return          A new driver object.
     */
    public Driver getDriver(String envUid, String driverUid) {
        return new Driver(this.getEnvironment(envUid), driverUid, this.requests);
    }
}


/**
 * Thread class that starts/stops a background Testplan interactive instance.
 * Retrieves the ip/port information of the underlying HTTP listener.
 */
class TestplanThread extends Thread {
    String interpreter;
    String testplanPath;
    Process proc;
    String ip;
    String port;

    public TestplanThread(String interpreter, String testplanPath) {
        super();
        this.interpreter = interpreter;
        this.testplanPath = testplanPath;
    }

    public synchronized void doStop() {
        this.proc.destroy();
        if (this.proc.exitValue() >= 0) {
            System.out.println("Testplan process exited.");
        }
    }

    public void run() {
        try {
            this.proc = Runtime.getRuntime().exec(
                    this.interpreter + " " + this.testplanPath + " --interactive");
            System.out.println("Proc: " + this.proc);

            Pattern pat = Pattern.compile(
                    ".* listening on: ([0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+):([0-9]+)");
            Matcher mat;
            InputStream stdout;
            String line;

            stdout = this.proc.getInputStream();
            BufferedReader brCleanUp =
                    new BufferedReader(new InputStreamReader(stdout));

            while ((line = brCleanUp.readLine()) != null) {
                mat = pat.matcher(line);
                if (mat.find()) {
                    this.ip = mat.group(1);
                    this.port = mat.group(2);
                    return;
                }
            }

        } catch (IOException e) {
            System.out.println("Could not start process.");
        }
    }
}
