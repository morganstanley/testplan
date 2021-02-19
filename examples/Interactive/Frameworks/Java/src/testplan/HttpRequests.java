/**
 * Containing class that performs HTTP requests.
 */

package testplan;

import java.io.*;
import java.util.HashMap;

import java.net.URL;
import java.net.HttpURLConnection;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;


/**
 * Performs HTTP requests to Testplan HTTP listener in a given address.
 */
public class HttpRequests {
    Gson gson;
    String ip;
    String port;

    public HttpRequests(String targetIp, String targetPort) {
        this.ip = targetIp;
        this.port = targetPort;
        this.gson = new GsonBuilder()
                .enableComplexMapKeySerialization().setPrettyPrinting().create();
    }

    /**
     * Make a post requests to Testplan listener that performs an operation
     * that the backend interactive supports. All arguments of that operation
     * will be passed as json.
     *
     * @param method Name of backend operation method.
     * @param data   Kwargs of the given method.
     * @return       Response Map received by the Testplan interactive HTTP handler.
     */
    public HashMap<String, Object> sendPost(
            String method, HashMap<String, Object> data) throws Exception {
        String url = "http://" + this.ip + ":" + this.port + method;
        URL obj = new URL(url);
        HttpURLConnection con = (HttpURLConnection) obj.openConnection();
        con.setRequestMethod("POST");
        con.setRequestProperty("Content-Type", "application/json");

        // Send the post request.
        con.setDoOutput(true);
        DataOutputStream wr = new DataOutputStream(con.getOutputStream());
        wr.write(this.gson.toJson(
                data,
                new TypeToken<HashMap<String, Object>>() {
                }.getType()).getBytes());
        wr.flush();
        wr.close();

        // Retrieve the response.
        BufferedReader in;
        int responseCode = con.getResponseCode();
        if (responseCode == 200) {
            in = new BufferedReader(new InputStreamReader(con.getInputStream()));
        } else {
            in = new BufferedReader(new InputStreamReader(con.getErrorStream()));
        }
        String inputLine;
        StringBuilder responseString = new StringBuilder();
        while ((inputLine = in.readLine()) != null) {
            responseString.append(inputLine);
        }
        in.close();
        HashMap<String, Object> responseMap = new HashMap<String, Object>();
        responseMap = this.gson.fromJson(
                responseString.toString(), responseMap.getClass());

        if (responseCode != 200) {
            System.out.println("\nPost request failure: " + url);
            System.out.println("Post data : " + data);
            System.out.println("Response Code : " + responseCode);
            System.out.println("POST Response Message : " + con.getResponseMessage());
            System.out.println("POST Response map: " + responseMap);
        }
        return responseMap;
    }
}
