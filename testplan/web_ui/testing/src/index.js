import React from 'react';
import ReactDOM from 'react-dom';
import BatchReportPrev from './Report/BatchReport.prev';
import BatchReport from './Report/BatchReport';
import InteractiveReport from './Report/InteractiveReport';
import EmptyReport from './Report/EmptyReport';
import {POLL_MS} from './Common/defaults.js';
import Home from './Common/Home';
import SwitchRequireSlash from './Common/SwitchRequireSlash';

// import registerServiceWorker from './registerServiceWorker';
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter, Route } from 'react-router-dom';

/**
 * This single App provides multiple functions controlled via the URL path
 * accessed. We are using React-Router to control which type of report is
 * rendered and to extract the report UID from the URL when necessary.
 */
const AppRouter = () => (
  <BrowserRouter>
    <SwitchRequireSlash>
      <Route exact path="/" component={Home} />
      <Route path="/testplan/:uid" render={props => (
        JSON.parse(new URLSearchParams(props.location.search).get('dev'))
          ? <BatchReport {...props} />
          : <BatchReportPrev {...props} />
      )} />
      {/*<Route path="/testplan/:uid" >
         <BatchReport />
      </Route>*/}
      <Route path="/interactive/_dev">
        <InteractiveReport dev={true} />
      </Route>
      <Route path="/interactive">
        <InteractiveReport dev={false} poll_ms={POLL_MS} />
      </Route>
      {/* Must be last */}
      <Route component={EmptyReport} />
    </SwitchRequireSlash>
  </BrowserRouter>
);

ReactDOM.render(<AppRouter />, document.getElementById('root'));
// registerServiceWorker();
