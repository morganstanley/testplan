import React from 'react';
import ReactDOM from 'react-dom';
import BatchReport from './Report/BatchReport';
import InteractiveReport from './Report/InteractiveReport';
import EmptyReport from './Report/EmptyReport';
import {POLL_MS} from './Common/defaults.js';
import Home from './Common/Home';

// import registerServiceWorker from './registerServiceWorker';
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter, Route, Switch, Redirect } from "react-router-dom";

/**
 * This single App provides multiple functions controlled via the URL path
 * accessed. We are using React-Router to control which type of report is
 * rendered and to extract the report UID from the URL when necessary.
 *
 * We use "strict" here to ensure that paths end with a trailing slash. This
 * makes the UI-rendered hash routes more distinguishable from the
 * server-rendered regular routes. The final <Route> catches URLs entered by
 * the user that don't contain a trailing slash, e.g. "/:url", and redirects
 * them to e.g. "/:url/".
 */
const AppRouter = () => (
  <BrowserRouter>
    <Switch>
      {/* Must be first - require trailing slash */}
      <Route strict exact
             from="(|.*?[^/])"
             component={props => (
                 <Redirect to={`${props.location.pathname}/`}/>
             )}
      />
      <Route exact path="/" component={Home} />
      <Route path="/testplan/:uid" component={BatchReport} />
      <Route path="/interactive/_dev">
        <InteractiveReport dev={true} />
      </Route>
      <Route path="/interactive">
        <InteractiveReport dev={false} poll_ms={POLL_MS} />
      </Route>
      {/* Must be last */}
      <Route component={EmptyReport} />
    </Switch>
  </BrowserRouter>
);

ReactDOM.render(<AppRouter />, document.getElementById('root'));
// registerServiceWorker();
