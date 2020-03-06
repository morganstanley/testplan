import React from "react";
import { Redirect } from "react-router-dom";

/**
 * When NODE_ENV === 'development' we can choose an actual report to render
 * by setting the environment variable REACT_APP_REPORT_GUID_OVERRIDE
 * to an actual report GUID.
 *
 * Note that process.env.REACT_APP_* vars are elided during compilation. See
 * node_modules/react-scripts/config/env.js:73.
 */
const DevHome = () => {
  const REPORT_GUID_OVERRIDE = process.env.REACT_APP_REPORT_GUID_OVERRIDE;
  if(typeof REPORT_GUID_OVERRIDE !== "undefined") {
    const dest = `/testplan/${REPORT_GUID_OVERRIDE}`;
    console.log(`REACT_APP_REPORT_GUID_OVERRIDE="${REPORT_GUID_OVERRIDE}" so redirecting to "${dest}"`);
    return <Redirect to={dest} />;
  } else {
    return (
      <>
        <h2 style={{ color: "green" }}>
          Set these environment variables before compiling:
          <ul>
            <li>REACT_APP_REPORT_GUID_OVERRIDE - GUID of an existing report</li>
            <li>
              REACT_APP_COUCHDB_HOST - Full 'scheme://host:port/path' of your couchdb server,
              e.g. 'http://couch.example.com/devel'
            </li>
          </ul>
          If your couchdb server has a different origin than your development server and doesn't have
          CORS configured, you'll need to launch chrome with the '--disable-web-security' flag to
          allow cross-origin requests.
        </h2>
      </>
    );
  }
};

const ProdHome = () => (
    <>
      <h2>Navigate to the test report link printed at the end of your testplan run.</h2>
    </>
);

// TODO: Make a homepage that is unconditionally useful
export default function Home() {
  return (
    <>
      <h1 style={{ color: "red" }}>NO TEST REPORT TO RENDER</h1>
      {process.env.NODE_ENV === "development" ? <DevHome /> : <ProdHome />}
    </>
  );
}