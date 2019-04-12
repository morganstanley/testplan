/**
 * Testplan environment package.
 */

package testplan.environment;

import testplan.environment.drivers.DriverEntry;

import java.util.HashMap;
import java.util.LinkedList;


/**
 * Class representing a collection of drivers and provides
 * methods for environment manipulation via HTTP requests.
 */
public class Environment {
    String uid;
    LinkedList<DriverEntry> drivers;

    /**
     * Create an environment with a list of drivers.
     *
     * @param envUid  Environment uid.
     * @param drivers List of driver entries.
     */
    public Environment(String envUid, LinkedList<DriverEntry> drivers) {
        this.uid = envUid;
        this.drivers = drivers;
    }

    /**
     * Returns the environment uid.
     */
    public String getUid() {
        return this.uid;
    }

    /**
     * Returns a list of driver entries.
     */
    public LinkedList<DriverEntry> getDrivers() {
        return this.drivers;
    }

    /**
     * Creates an HTTP request to start an environment.
     */
    public HashMap<String, Object> startEnvironmentRequest() {
        HashMap<String, Object> data = new HashMap<String, Object>();
        data.put("operation", "start_environment");
        data.put("env_uid", this.uid);
        return data;
    }

    /**
     * Creates an HTTP request to stop an environment.
     */
    public HashMap<String, Object> stopEnvironmentRequest() {
        HashMap<String, Object> data = new HashMap<String, Object>();
        data.put("operation", "stop_environment");
        data.put("env_uid", this.uid);
        return data;
    }

    /**
     * Bundle all HTTP requests needed to create an environment with
     * added driver resource entries.
     *
     * @return A list of HTTP requests data to be performed.
     */
    public LinkedList<HashMap<String, Object>> addEnvironmentRequests() {
        LinkedList<HashMap<String, Object>> result =
                new LinkedList<HashMap<String, Object>>();
        HashMap<String, Object> data = new HashMap<String, Object>();
        data.put("env_uid", this.uid);
        data.put("operation", "create_new_environment");
        result.addLast(data);

        for (DriverEntry driver : this.drivers) {
            data = new HashMap<String, Object>();
            data.put("env_uid", this.uid);
            data.put("target_class_name", driver.getType());
            HashMap<String, Object> kwargs = driver.getKwargs();
            for (String arg : kwargs.keySet()) {
                data.put(arg, kwargs.get(arg));
            }
            data.put("operation", "add_environment_resource");
            result.addLast(data);
        }

        data = new HashMap<String, Object>();
        data.put("env_uid", this.uid);
        data.put("operation", "add_created_environment");
        result.addLast(data);
        return result;
    }

    /**
     * HTTP request for adding a driver in this environment.
     *
     * @param driver Driver to be added.
     */
    public HashMap<String, Object> addDriverRequest(DriverEntry driver) {
        HashMap<String, Object> data = new HashMap<String, Object>();
        data.put("env_uid", this.uid);
        data.put("target_class_name", driver.getType());
        data.put("operation", "add_environment_resource");
        HashMap<String, Object> kwargs = driver.getKwargs();
        for (String arg : kwargs.keySet()) {
            data.put(arg, kwargs.get(arg));
        }
        this.drivers.addLast(driver);
        return data;
    }

    /**
     * Driver context value retrieval HTTP request.
     *
     * @param driverUid    Driver uid.
     * @param context_item Context item to lookup.
     * @return             HTTP request data.
     */
    public HashMap<String, Object> getContextValueRequest(String driverUid, String context_item) {
        HashMap<String, Object> data = new HashMap<String, Object>();
        data.put("env_uid", this.uid);
        data.put("resource_uid", driverUid);
        data.put("context_item", context_item);
        data.put("operation", "environment_resource_context");
        return data;
    }

    /**
     * Generate HTTP request to perform an actual driver operation.
     *
     * @param driverUid       Driver uid.
     * @param driverOperation Target driver operation (method name).
     * @param operationData   Kwargs for driver operation (method name).
     * @return                HTTP request data.
     */
    public HashMap<String, Object> driverOpsRequest(
            final String driverUid, final String driverOperation,
            HashMap<String, Object> operationData) {
        final String envuid = this.uid;
        HashMap<String, Object> data = new HashMap<String, Object>() {{
            this.put("env_uid", envuid);
            this.put("resource_uid", driverUid);
            this.put("res_op", driverOperation);
        }};
        for (String key : operationData.keySet()) {
            data.put(key, operationData.get(key));
        }
        return data;
    }
}
