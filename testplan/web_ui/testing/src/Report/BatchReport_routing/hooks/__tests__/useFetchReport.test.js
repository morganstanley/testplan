/** @jest-environment jsdom */
// @ts-nocheck
import moxios from 'moxios';
import { cleanup, renderHook } from 'react-hooks-testing-library';
import useReportState from '../useReportState';

jest.mock('../useReportState');

describe('useFetchReport', () => {

  beforeAll(() => {
    global.env = {
      reportUid: '0123456789abcdeffedcba9876543210',
      setJsonReport: jest.fn().mockName('setAppBatchReportJsonReport'),
      setLoading: jest.fn().mockName('setAppBatchReportIsLoading'),
      setFetching: jest.fn().mockName('setAppBatchReportIsFetching'),
      setFetchError: jest.fn().mockName('setAppBatchReportFetchError'),
      'api.baseURL': 'http://ptth.iq/api',
      'api.headers': { 'X-Useless-Header': '1' },
    };
    useReportState.mockReturnValue([
      [
        global.env['api.baseURL'],
        global.env['api.headers'],
      ],
      [
        global.env.setJsonReport,
        global.env.setLoading,
        global.env.setFetching,
        global.env.setFetchError,
      ],
    ]).mockName('useReportState');
  });

  it('cancels pending fetches when unmounted', done => {
    return new Promise((mockResolve, mockReject) => {
      let mockUnmount = null;
      jest.mock('axios', () =>  {
        const __CancelToken_source_rv = {
          token: 'MOCK_CANCEL_TOKEN',
          cancel: jest.fn().mockName('cancel'),
        };
        return {
          __esModule: true,
          __CancelToken_source_rv,
          default: {
            create: jest.fn(() => ({
              get: jest.fn(() => new Promise((resolve, reject) => {
                // we use `setImmediate` to ensure all promises are
                // resolved / rejected in exactly the right order
                setImmediate(() => {
                  if(mockUnmount === null) {
                    mockReject(
                      "somehow we got to the mocked " +
                      "`Axios.create().get()` without `mockUnmount` " +
                      "getting set to the `renderHook` function's " +
                      "returned `unmount` function."
                    );
                    reject();
                  } else {
                    // ensure promise is resolved immediately after unmount
                    mockUnmount();
                    mockResolve();
                    resolve();
                  }
                });
              })).mockName('get'),
            })).mockName('create'),
            CancelToken: {
              source: jest.fn(() => {
                return __CancelToken_source_rv;
              }).mockName('source'),
            },
            isCancel: jest.fn(),
          },
        };
      });
      const { default: useFetchReport } = require('../useFetchReport');
      mockUnmount = renderHook(
        () => useFetchReport(global.env.reportUid)
      ).unmount;
      setTimeout(() => {  // safeguard to fail after 15 sec
        mockReject('Timed out waiting for unmount');
      }, 15000);
    }).then(() => {
      const { __CancelToken_source_rv } = require('axios');
      expect(__CancelToken_source_rv.cancel).toHaveBeenCalledTimes(1);
      done();
    }).catch(errMsg => {
      done(new Error(errMsg));
    });
  });

  describe('interacting with moxios API', () => {

    beforeEach(() => {
      const { default: Axios } = require('axios');
      global.env.axiosInstance = Axios.create();
      moxios.install(global.env.axiosInstance);
      const { default: useFetchReport } = require('../useFetchReport');
      global.env.rendered = renderHook(
      // global.env.rendered = renderHook(
        ({ reportUid, isDev, skipFetch, axiosInstance }) => {
          return useFetchReport(reportUid, isDev, skipFetch, axiosInstance);
        },
        {
          initialProps: {
            reportUid: global.env.reportUid,
            isDev: false,
            skipFetch: false,
            axiosInstance: global.env.axiosInstance
          }
        }
      );
    });

    it('passes received report to `setAppBatchReportJsonReport`', done => {
      return moxios.wait(() => {
        const request = moxios.requests.mostRecent();
        request.respondWith({
          status: 200,
          response: { entries: [] },
        }).then(response => {
          const { setJsonReport } = global.env;
          expect(setJsonReport).toHaveBeenCalledTimes(1);
          expect(setJsonReport).toHaveBeenLastCalledWith(response.data);
          done();
        }).catch(err => {
          done(err);
        });
      });
    });

    it('passes request errors to `setFetchErrorCb`', done => {
      return moxios.wait(() => {
        const request = moxios.requests.mostRecent();
        request.respondWith({
          status: 401,
          response: { entries: [] },
        }).then(response => {
          const { setFetchError } = global.env;
          expect(setFetchError).toHaveBeenCalledTimes(1);
          const call_0_arg_0 = setFetchError.mock.calls[0][0];
          expect(call_0_arg_0).toBeInstanceOf(Error);
          expect(call_0_arg_0.response).toBe(response);
          done();
        }).catch(err => {
          done(err);
        });
      });
    });

    it('passes non-request errors to `setFetchErrorCb`', done => {
      return moxios.wait(() => {
        const request = moxios.requests.mostRecent();
        request.respondWith({
          status: 200,
          response: { entries: null },  // error's thrown from PropagateIndices
        }).then(() => {
          const { setFetchError } = global.env;
          expect(setFetchError).toHaveBeenCalledTimes(1);
          const call_0_arg_0 = setFetchError.mock.calls[0][0];
          expect(call_0_arg_0).toBeInstanceOf(Error);
          done();
        }).catch(err => {
          done(err);
        });
      });
    });

    afterEach(() => {
      cleanup();
      moxios.uninstall(global.env.axiosInstance);
    });

  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  afterAll(() => {
    delete global.env;
  });

});
