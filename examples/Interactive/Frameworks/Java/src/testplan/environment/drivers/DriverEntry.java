package testplan.environment.drivers;

import java.util.HashMap;

/**
 * Drier entry containing initialisation info for a driver.
 */
public class DriverEntry {
    String type;
    String uid;
    HashMap<String, Object> kwargs;

    /**
     * Sets the target driver information.
     *
     * @param driverType Equivalent python driver class.
     * @param driverArgs Arguments for actual driver constructor.
     */
    public DriverEntry(String driverType, HashMap<String, Object> driverArgs) {
        this.type = driverType;
        this.kwargs = driverArgs;
        this.uid = (String) driverArgs.get("name");
    }

    public String getType() {
        return this.type;
    }

    public String getUid() {
        return this.uid;
    }

    public HashMap<String, Object> getKwargs() {
        return this.kwargs;
    }

    public Object getArg(String key) {
        return this.kwargs.get(key);
    }
}
