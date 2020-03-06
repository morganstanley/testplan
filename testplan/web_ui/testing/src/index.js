import React from 'react';
import ReactDOM from 'react-dom';
import BatchReport from './Report/BatchReport';
import BatchReportBeta from './Report/BatchReportBeta';
import InteractiveReport from './Report/InteractiveReport';
import EmptyReport from './Report/EmptyReport';
import {POLL_MS} from './Common/defaults.js';

// import registerServiceWorker from './registerServiceWorker';
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter as Router, Route, Switch } from "react-router-dom";

/**
 * This single App provides multiple functions controlled via the URL path
 * accessed. We are using React-Router to control which type of report is
 * rendered and to extract the report UID from the URL when necessary.
 */
const AppRouter = () => (
  <Router>
    <Switch>
      <Route path="/testplan/beta/1004/:uid" component={BatchReportBeta} />
      <Route path="/testplan/:uid" component={BatchReport} />
      <Route path="/interactive/_dev">
        <InteractiveReport dev={true} />
      </Route>
      <Route path="/interactive">
        <InteractiveReport dev={false} poll_ms={POLL_MS} />
      </Route>
      <Route component={EmptyReport} />
    </Switch>
  </Router>
);

ReactDOM.render(<AppRouter />, document.getElementById('root'));
// registerServiceWorker();
