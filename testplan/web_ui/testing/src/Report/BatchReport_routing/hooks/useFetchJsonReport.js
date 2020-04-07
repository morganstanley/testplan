import React from 'react';
import Axios from 'axios';
import _cloneDeep from 'lodash/cloneDeep';
import { PropagateIndices } from '../../reportUtils';
import useReportState from './useReportState';

export default function useFetchJsonReport(
  reportUid, isDev = false, skipFetch = false, axiosInstance = null
) {
  const [
      [ apiBaseURL, apiHeaders ],
      [ setJsonReport, setLoading, setFetching, setFetchError ]
    ] = useReportState(
    [ 'api.baseURL', 'api.headers' ],
    [
      'setAppBatchReportJsonReport',
      'setAppBatchReportIsLoading',
      'setAppBatchReportIsFetching',
      'setAppBatchReportFetchError',
    ]),
    setJsonReportCb = React.useCallback(setJsonReport, []),
    setLoadingCb = React.useCallback(setLoading, []),
    setFetchingCb = React.useCallback(setFetching, []),
    setFetchErrorCb = React.useCallback(setFetchError, []),
    currAxiosInstance = React.useMemo(() => axiosInstance || Axios.create({
      baseURL: apiBaseURL,
      headers: apiHeaders,
    }), [ axiosInstance, apiBaseURL, apiHeaders ]);

  const fetchRealReport = React.useCallback(() => {
    const fetchCanceller = Axios.CancelToken.source();
    (async () => {
      setLoadingCb(true);
      let isCancelled = false;
      try {
        setFetchingCb(true);
        const document = await currAxiosInstance.get(`/reports/${reportUid}`, {
          cancelToken: fetchCanceller.token,
        });
        setFetchingCb(false);
        const report = _cloneDeep(document.data);
        const propagatedReport = PropagateIndices(report);
        setJsonReportCb(propagatedReport);
      } catch(err) {
        if(!Axios.isCancel(err)) { // can't set state after cleanup func runs
          setFetchErrorCb(err);
        } else {
          isCancelled = true;
          console.error(err);
        }
      }
      if(!isCancelled) {
        setLoadingCb(false);
        setFetchingCb(false);
      }
    })();
    return () => {  // cleanup func: cancel any pending fetches on unmount
      fetchCanceller.cancel('Fetch cancelled due to component cleanup');
    };
  }, [
    currAxiosInstance, reportUid, setLoadingCb, setFetchingCb, setJsonReportCb,
    setFetchErrorCb,
  ]);

  const fetchFakeReport = React.useCallback(() => {
    (async () => {
      try {
        setLoadingCb(true);
        setFetchingCb(true);
        const fakeAssertions = await import('../../../Common/fakeReport').then(
          fakeReport => fakeReport.fakeReportAssertions
        );
        setFetchingCb(false);
        // @ts-ignore
        const propagatedFakeAssertions = PropagateIndices(fakeAssertions);
        setJsonReportCb(propagatedFakeAssertions);
        setLoadingCb(false);
      } catch(err) {
        setFetchErrorCb(err);
        setLoadingCb(false);
        setFetchingCb(false);
      }
    })();
  }, [ setLoadingCb, setFetchingCb, setJsonReportCb, setFetchErrorCb ]);

  React.useEffect(() => (
    skipFetch
      ? undefined
      : isDev === true /* dont allow "truthy" values */
      ? fetchFakeReport()
      : fetchRealReport()
  ), [ isDev, fetchFakeReport, fetchRealReport, skipFetch ]);
}
