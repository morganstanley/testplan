import { useCallback, useMemo, useEffect } from 'react';
import Axios from 'axios';
import _cloneDeep from 'lodash/cloneDeep';
import { PropagateIndices } from '../../reportUtils';
import useReportState from './useReportState';

export default function useFetchReport(
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
    setJsonReportCb = useCallback(setJsonReport, []),
    setLoadingCb = useCallback(setLoading, []),
    setFetchingCb = useCallback(setFetching, []),
    setFetchErrorCb = useCallback(setFetchError, []),
    currAxiosInstance = useMemo(() => axiosInstance || Axios.create({
      baseURL: apiBaseURL,
      headers: apiHeaders,
    }), [ axiosInstance, apiBaseURL, apiHeaders ]);

  const fetchRealReport = useCallback(() => {
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

  let fetchFakeReport;
  if(process.env.NODE_ENV !== 'production') {
    fetchFakeReport = () => {
      (async () => {
        try {
          setLoadingCb(true);
          setFetchingCb(true);
          const fakeAssertions = await import(
            '../../../__tests__/mocks/documents/fakeReportAssertions.json'
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
    };
  }

  useEffect(() => {
    if(process.env.NODE_ENV !== 'production') {
      return skipFetch
        ? undefined
        : isDev === true /* dont allow "truthy" values */
          ? fetchFakeReport()
          : fetchRealReport();
    }
    return fetchRealReport();
  }, [ isDev, fetchRealReport, skipFetch ]);
}
