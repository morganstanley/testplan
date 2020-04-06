/* global import */
/// <reference lib="webworker" />
import axios from 'axios';

function getAxiosConfig(xtraConfig = {}) {
  const axiosConf = { headers: {}, ...xtraConfig };
  try {
    if(process.env.NODE_ENV === 'development') {
      let dbOverride = null;
      try {
        dbOverride = process.env.REACT_APP_API_BASE_URL;
      } catch(err) {
        console.error(err);
      }
      if(dbOverride) {
        // @ts-ignore
        axiosConf.baseURL = dbOverride;
        const dbOverrideOrigin = new URL(dbOverride).origin;
        if(window.location.origin !== dbOverrideOrigin) {
          // CORS headers: developer.mozilla.org/en-US/docs/Web/HTTP/CORS
          axiosConf.headers['Access-Control-Allow-Origin'] = dbOverrideOrigin;
        }
      }
    }
  } catch(err) {
    console.error(err);
    return {};
  }
  return axiosConf;
}

function getUidOverride() {
  try {
    return process.env.REACT_APP_REPORT_UID_OVERRIDE;
  } catch(err) {
    return null;
  }
}

function noop(...x) {}

export default async function fetchReport({
  reportUid, setReport, isDev = false, cancelToken = null, setCancel = noop,
  setLoading = noop, setFetching = noop, setFetchError = noop,
  setMessage = noop
}) {
  setMessage('>>> Starting fetch...');
  setLoading(true);
  try {
    const axiosConfig = getAxiosConfig(cancelToken ? { cancelToken } : {});
    setFetching(true);
    const report = (
      isDev && !getUidOverride()
        // importing like this means webpack *may* exclude fakeReport.js
        // from the production bundle
        ? (await import('../../../Common/fakeReport')).fakeReportAssertions
        : await axios.get(
          `/api/v1/reports/${reportUid}`,
          axiosConfig
        )
    );
    setFetching(false);
    // @ts-ignore
    setReport(report.data);
  } catch(err) {
    if(axios.isCancel(err)) {
      setCancel(err);
    } else {
      setFetchError(err);
    }
  }
  setLoading(false);
  setMessage('>>> Ending fetch...');
}

/* eslint-env worker, es6, commonjs */
/* eslint-disable no-restricted-globals */
if(self.constructor.name === 'DedicatedWorkerGlobalScope') {
  // @ts-ignore
  self.import = self.importScripts;
  let msgId = 0;
  const send = msg => postMessage({
    ...msg, id: ++msgId, time: new Date().toISOString()
  });
  const msgStore = [];
  const messageRecorder = msg => {
    msgStore.push(msg);
    console.debug(msg);
  };
  (async () => {
    try {
      await new Promise((resolve, reject) => {
        let awaitParams;
        function requestParams() {
          const reqParam = (param, required = true) => ({ param, required });
          const request = [
            reqParam('reportUid'),
            reqParam('isDev', false)
          ];
          const timeout = 20_000,
                interval = 5_000;
          const intervalId = setInterval(
            async () => send({ request }),
            interval
          );
          const timeoutId = setTimeout(() => {
              clearInterval(intervalId);
              removeEventListener('message', awaitParams);
              reject({ timeout });
            },
            timeout
          );
          return (evt) => {
            messageRecorder(evt.data);
            // check we have requireds
            if(typeof evt.data === 'object' && request.filter(e => e.required)
              .map(e => e.param).every(p => ~Object.keys(evt.data).indexOf(p))
            ) {
              clearTimeout(timeoutId);
              clearInterval(intervalId);
              removeEventListener('message', awaitParams);
              const allParams = request.map(e => e.param);
              resolve(Object.fromEntries(  // remove extraneous entries
                Object.entries(evt.data)
                  .filter(([k]) => ~allParams.indexOf(k))
              ));
            }
          };
        }
        addEventListener('message', (awaitParams = requestParams()));
      }).then(async data => {
        const justLog = evt => messageRecorder(evt.data);
        addEventListener('message', justLog);
        let cancelFunc;
        const fetching = fetchReport({
          reportUid: data.reportUid,
          isDev: data.isDev || false,
          cancelToken: new axios.CancelToken(c => { cancelFunc = c; }),
          setReport: report => send({report}),
          setLoading: isLoading => send({isLoading}),
          setFetching: isFetching => send({isFetching}),
          setFetchError: fetchError => send({fetchError}),
          setMessage: message => send({message}),
          setCancel: cancel => send({cancel}),
        });
        const monitor = async evt => {
          messageRecorder(evt.data);
          if((evt.data.message || '').toLowerCase() === 'abort') {
            send({ status: 'aborting' });
            cancelFunc();
            await fetching;
            send({ status: 'aborted' });
          }
        };
        removeEventListener('message', justLog);
        addEventListener('message', monitor);
        await fetching;
        send({ complete: 'complete' });
      }).catch(error => {
        send({ error });
      });
    } catch(error) {
      send({ error });
    }
  })();
}
/* eslint-env browser, es6, commonjs */
/* eslint-enable no-restricted-globals */
