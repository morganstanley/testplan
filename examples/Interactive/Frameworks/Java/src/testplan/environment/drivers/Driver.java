package testplan.environment.drivers;

import testplan.HttpRequests;
import testplan.environment.Environment;

import java.util.HashMap;

/**
 * Class to be used to perform actual driver operations.
 */
public class Driver {
    HttpRequests requests;
    String operation;
    HashMap<String, Object> kwargs;
    Environment env;
    String driverUid;

    /**
     * Constructor method.
     *
     * @param env       Environment holding the driver.
     * @param driverUid Driver uid.
     * @param requests  Object that performs http requests.
     */
    public Driver(Environment env, String driverUid, HttpRequests requests) {
        this.env = env;
        this.driverUid = driverUid;
        this.requests = requests;
        this.kwargs = new HashMap<String, Object>();
    }

    /**
     * Adds the operation field used in the HTTP request.
     * @param methodName Target python driver method name.
     */
    public Driver method(String methodName) {
        this.operation = methodName;
        return this;
    }

    /**
     * Add an input  keyword argument for method specified.
     * @param key   Methods argument key.
     * @param value Methods argument value.
     */
    public Driver kwarg(String key, Object value) {
        this.kwargs.put(key, value);
        return this;
    }

    /**
     * Send an HTTP requests to trigger the driver operation specified
     * using .method() and .kwarg() methods and returns the result.
     */
    public Object exec() throws Exception {
        HashMap<String, Object> data = env.DriverOpsRequest(
                driverUid, this.operation, this.kwargs);
        return this.requests.sendPost(
                "/sync/environment_resource_operation", data).get("result");
    }
}
