import React from 'react';
import { connect, Provider } from 'react-redux';
import { Router } from 'react-router';
import CenterPane from './components/CenterPane';
import Toolbar from './components/Toolbar';
import uiHistory from './state/uiHistory';
import NavPanes from './components/NavPanes';
import { BATCH_REPORT_CLASSES } from './styles';
import { fetchReport } from './state/reportActions';
import store from './state/store';

const __DEV__ = process.env.NODE_ENV !== 'production';

const connector = connect(
  null,
  function mapDispatchToProps(dispatch) {
    return {
      boundFetchReport: arg => dispatch(fetchReport(arg)),
    };
  },
);

const BatchReportInner = ({ children = null, ...props }) => {
  const { boundFetchReport, uid, axios, testReport } = props;
  React.useEffect(() => {
    const arg = { axios };
    if(testReport && __DEV__) arg.testReport = testReport;
    else arg.uid = uid;
    // this `.abort()` function will be called when this component unmounts,
    // thus cancelling any outstanding requests
    return boundFetchReport(arg).abort;
  }, [ testReport, uid, boundFetchReport, axios ]);
  return (
    <div className={BATCH_REPORT_CLASSES}>
      <Toolbar/>
      <NavPanes/>
      <CenterPane/>
      {children}
    </div>
  );
};

const ConnectedBatchReportInner = connector(BatchReportInner);

export default function BatchReport({ match, axios, testReport, ...props }) {
  return (
    <Provider store={store}>
      <Router history={uiHistory}>
        <ConnectedBatchReportInner uid={match.params.uid}
                                   axios={axios}
                                   testReport={testReport}
                                   {...props}
        />
      </Router>
    </Provider>
  );
}
