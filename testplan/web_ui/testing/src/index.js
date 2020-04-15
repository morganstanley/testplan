import 'bootstrap/dist/css/bootstrap.min.css';
import React, { Suspense, lazy } from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter, Route } from 'react-router-dom';
import { FadeLoader } from 'react-spinners';
import { POLL_MS } from './Common/defaults.js';
import SwitchRequireSlash from './Common/SwitchRequireSlash';

// Don't make users download scripts that they won't use.
// see: https://reactjs.org/docs/code-splitting.html#route-based-code-splitting
const BatchReport = lazy(() => import('./Report/BatchReport'));
const BatchReport_routing = lazy(() => import('./Report/BatchReport_routing'));
const InteractiveReport = lazy(() => import('./Report/InteractiveReport'));
const EmptyReport = lazy(() => import('./Report/EmptyReport'));
const Home = lazy(() => import('./Common/Home'));
const LoadingAnimation = () => (
  <div style={
    // Used to center spinner on page,suggested by
    // github.com/davidhu2000/react-spinners/issues/53#issuecomment-472369554
    {
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    }
  }>
    <FadeLoader height={15} width={5} radius={10}/>
  </div>
);

/**
 * This single App provides multiple functions controlled via the URL path
 * accessed. We are using React-Router to control which type of report is
 * rendered and to extract the report UID from the URL when necessary.
 */
const AppRouter = () => (
  <BrowserRouter>
    <Suspense fallback={<LoadingAnimation/>}>
      <SwitchRequireSlash>
        <Route exact path="/" component={Home} />
        <Route path="/testplan/:uid" render={props =>
          // eslint-disable-next-line max-len
          JSON.parse(new URLSearchParams(props.location.search).get('dev') || '')
            ? <BatchReport_routing {...props} />  // eslint-disable-line react/jsx-pascal-case, max-len
            : <BatchReport {...props} />
        } />
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
    </Suspense>
  </BrowserRouter>
);

ReactDOM.render(<AppRouter />, document.getElementById('root'));
