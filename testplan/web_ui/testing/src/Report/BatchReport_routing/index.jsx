import React from 'react';
import _isEqual from 'lodash/isEqual';
import { css } from 'aphrodite';
import Axios from 'axios';
import { useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';

import CenterPane from './components/CenterPane';
import Toolbar from './components/Toolbar';
import { batchReportStyles } from './style';
import ReportStateProvider from './state/ReportStateProvider';
import useReportState from './hooks/useReportState';
import useFetchJsonReport from './hooks/useFetchJsonReport';
import UIRouter from './components/UIRouter';
import NavPanes from './components/NavPanes';
import { queryStringToMap } from './utils';

export function BatchReportStartup({
  browserProps,
  children = null,
  skipFetch = false,
  axiosInstance = null,
}) {
  const
    currLocation = useLocation(),
    [, [ mapHashQueryToState, mapQueryToState ]] = useReportState(false, [
      'mapUriHashQueryToState', 'mapUriQueryToState'
    ]),
    uriQueryMap = queryStringToMap(
      // `browserProps.location` may not exist during tests
      browserProps.location ? browserProps.location.search : ''
    ),
    uriHashQueryMap = queryStringToMap(currLocation.search),
    isDevelopment =
      process.env.NODE_ENV === 'development' && !!uriQueryMap.dev,
    isTesting =
      process.env.NODE_ENV === 'testing' && !!uriQueryMap.isTesting;

  // always sync on first render
  const isFirstRenderRef = React.useRef(true);
  if(isFirstRenderRef.current) {
    mapHashQueryToState(uriHashQueryMap);
    mapQueryToState(uriQueryMap);
    isFirstRenderRef.current = false;
  }

  // sync query params to state when they change
  const prevQueryMapRef = React.useRef(uriHashQueryMap);
  if(!_isEqual(uriQueryMap, prevQueryMapRef.current)) {
    mapQueryToState(uriQueryMap);
    prevQueryMapRef.current = uriQueryMap;
  }

  // sync hash query params to state when they change
  const prevHashQueryMapRef = React.useRef(uriHashQueryMap);
  if(!_isEqual(uriHashQueryMap, prevHashQueryMapRef.current)) {
    mapHashQueryToState(uriHashQueryMap);
    prevHashQueryMapRef.current = uriHashQueryMap;
  }

  useFetchJsonReport(
    browserProps.match.params.uid,
    isDevelopment || isTesting,
    skipFetch,
    axiosInstance,
  );

  return children;
}
BatchReportStartup.propTypes = {
  browserProps: PropTypes.shape({
    match: PropTypes.object,
    location: PropTypes.object,
    history: PropTypes.object,
  }).isRequired,
  children: PropTypes.element,
  axiosInstance: PropTypes.oneOf([
    PropTypes.instanceOf(Axios),
    null,
  ]),
};

export default function BatchReport(props) {
  const browserProps = {
    match: props.match,
    location: props.location,
    history: props.history,
  };
  return (
    <ReportStateProvider>
      <UIRouter>
        <BatchReportStartup browserProps={browserProps}
                            skipFetch={props.skipFetch}
                            axiosInstance={props.axiosInstance}
        >
          <div className={css(batchReportStyles.batchReport)}>
            <Toolbar/>
            <NavPanes/>
            <CenterPane/>
          </div>
        </BatchReportStartup>
      </UIRouter>
    </ReportStateProvider>
  );
}
BatchReport.propTypes = {
  // in testing we pass a shared ReportStateProvider to the component
  contextProvider: PropTypes.oneOf([
    'TestStateProvider',
  ]),
  props: PropTypes.shape({
    // may skip fetch during testing
    skipFetch: PropTypes.bool,
    // may be a moxios instance during testing
    axiosInstance: PropTypes.instanceOf(Axios),
  }),
};
