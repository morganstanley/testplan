import React from "react";
import { Redirect, useLocation } from "react-router-dom";

const NoReport = () => (
  <h1 style={{ color: "red" }}>NO TEST REPORT TO RENDER</h1>
);

/**
 * When NODE_ENV === 'development' we can choose an actual report to render
 * by setting the environment variable REACT_APP_REPORT_UID_OVERRIDE
 * to an actual report UID.
 *
 * Note that process.env.REACT_APP_* vars are elided during compilation. See
 * node_modules/react-scripts/config/env.js:73.
 */
const DevHome = () => {
  const REPORT_UID_OVERRIDE = process.env.REACT_APP_REPORT_UID_OVERRIDE;
  const { search: query, hash} = useLocation();
  if(typeof REPORT_UID_OVERRIDE !== "undefined") {
    // see CodeSandbox 'example.js' here:
    // https://reacttraining.com/react-router/web/example/query-parameters
    const dest = `/testplan/${REPORT_UID_OVERRIDE}${query}${hash}`;
    console.log(`REACT_APP_REPORT_UID_OVERRIDE="${REPORT_UID_OVERRIDE}" ` +
                `so redirecting to "${dest}"`);
    return <Redirect to={dest} />;
  } else {
    return (
      <>
        <NoReport/>
        <h2 style={{ color: "green" }}>
          Set these environment variables before compiling:
          <ul>
            <li>
              REACT_APP_REPORT_UID_OVERRIDE - UID of an existing report
            </li>
            <li>
              REACT_APP_API_BASE_URL - Full 'scheme://host:port/path' of your
              API server, e.g. 'http://couch.example.com/devel'
            </li>
          </ul>
          If your database server has a different origin than your development
          server and doesn't have CORS configured, you'll need to launch a
          newer Chrome / Chromium with the '--disable-web-security' flag to
          allow cross-origin requests.
        </h2>
      </>
    );
  }
};

const ProdHome = () => (
    <>
      <NoReport/>
      <h2>
        Navigate to the test report link printed at the end of your testplan
        run.
      </h2>
    </>
);

// TODO: Make a homepage that is unconditionally useful
export default function Home() {
  return (
    <>
      {process.env.NODE_ENV === "development" ? <DevHome /> : <ProdHome />}
    </>
  );
}
