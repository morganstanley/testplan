/// <reference types="jest" />
/* eslint-env jest */
import 'react-app-polyfill/stable';
import React from 'react';
import ReactTestUtils from 'react-dom/test-utils';
import { mount, configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import { StyleSheetTestUtils } from "aphrodite";
import moxios from 'moxios';
import { BrowserRouter, Route } from 'react-router-dom';

import ReportStateProvider from '../state/ReportStateProvider';
import ReportStateContext from '../state/ReportStateContext';
import BatchReport from '../';
import UIRouter from '../components/UIRouter';
import Message from '../../../Common/Message';
import { COLUMN_WIDTH } from '../../../Common/defaults';
import { TESTPLAN_REPORT, SIMPLE_REPORT } from "../../../Common/sampleReports";
import SwitchRequireSlash from '../../../Common/SwitchRequireSlash';

configure({ adapter: new Adapter() });

describe('BatchReport', () => {

  // this is only used to force a rerender of TestAppStateProvider by providing
  // different props each time
  let dummyCounter = 0;
  class TestStateProvider extends React.Component {
    intercepted = {
      appState: null,
      appActions: null,
      browserRouterProps: null,
      uiRouterProps: null,
    };
    interceptors = {
      appContext(val) {
        this.intercepted.appState = val[0];
        this.intercepted.appActions = val[1];
        return null;
      },
      browserRouterProps(val) {
        this.intercepted.browserRouterProps = val;
        return null;
      },
      uiRouterProps(val) {
        this.intercepted.uiRouterProps = val;
        return null;
      }
    };
    constructor(props) { super(props); }
    render() {
      return (
        <BrowserRouter>
          <SwitchRequireSlash location={this.props.location || null}>
            <Route path="/testplan/:uid" render={props => {
              this.interceptors.browserRouterProps(props);
              return (
                <ReportStateProvider>
                  <ReportStateContext.Consumer children={this.interceptors.appContext}/>
                  <UIRouter>
                    <Route render={this.interceptors.uiRouterProps} />
                    <BatchReport browserProps={props}
                                 skipFetch={this.props.skipFetch}
                                 axiosInstance={this.props.axiosInstance}
                    />
                  </UIRouter>
                </ReportStateProvider>
              );
            }}/>
          </SwitchRequireSlash>
        </BrowserRouter>
      );
    }
  }

  /** @returns {[ any, any ]} */
  function appStateAccessor() {
    class AppContextAccessor extends React.Component {
      constructor(props) { super(props); }
      render = () => (
        <ReportStateProvider>
          <ReportStateContext.Consumer>
            { /** @param {any} ctx */ ctx => (this.state = ctx) && null }
          </ReportStateContext.Consumer>
        </ReportStateProvider>
      );
    }
    // @ts-ignore
    return mount(<AppContextAccessor/>).instance().state;
  }

  /**
   * @property {string} uid
   * @property {any[]} props
   */
  const renderBatchReport = ({
    _dummyCounter = dummyCounter, uid = "123", ...props } = {}) => {
    // Mock the match object that would be passed down from react-router.
    // BatchReport uses this object to get the report UID.
    const mockMatch = { params: { uid: uid } };
    const startLocation = { pathname: uid ? `/testplan/${uid}` : null };
    return mount(
      /*
      // @ts-ignore
      <BatchReport match={mockMatch}
                   // contextProvider={SharedAppStateProviderInstance}
                   // _dummyRerenderer={dummyCounter++}
                   {...props} />
       */
      <TestStateProvider location={startLocation} {...props} />
    );
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    moxios.install();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    moxios.uninstall();
  });

  it('shallow renders without crashing', () => {
    renderBatchReport();
  });

  it('shallow renders the correct HTML structure when report loaded', () => {
    // @ts-ignore
    const batchReport = renderBatchReport({ skipFetch: true }),
      [, { setAppBatchReportJsonReport } ] = appStateAccessor();
    ReactTestUtils.act(
      () => setAppBatchReportJsonReport(TESTPLAN_REPORT)
    );
    batchReport.update();
    expect(batchReport).toMatchSnapshot();
  });

  it('renders loading message when fetching report', () => {
    let BR = mount(
      <TestStateProvider /*location={startLocation}*/ skipFetch={true} />
    );
    // @ts-ignore
    // let BR = renderBatchReport({ skipFetch: true });
    /*,
      [ appState, { setAppBatchReportIsFetching } ] = appStateAccessor(),
      isFetchingMessage = appState.app.reports.batch.isFetchingMessage;*/
    const
      setAppBatchReportIsFetching =
      BR.instance().intercepted.appActions.setAppBatchReportIsFetching,
      isFetchingMessage =
      BR.instance().intercepted.appState.app.reports.batch.isFetchingMessage;
    ReactTestUtils.act(() => {
      setAppBatchReportIsFetching(true);
      // dummyCounter++;
      // ReportStateContext.forceUpdate();
      BR.update();
    });
    // batchReport = renderBatchReport({ skipFetch: true });
    const messageDOM = mount(<Message left={COLUMN_WIDTH} message={isFetchingMessage} />).instance();
    const ass = BR.containsMatchingElement(
      // messageDOM
      <Message left={COLUMN_WIDTH} message={isFetchingMessage} />
    );
    expect(ass).toBe(true);
    let x = 1;
  });

  it('renders waiting message when waiting to start fetch', () => {
    // @ts-ignore
    const batchReport = renderBatchReport({ skipFetch: true }),
      [ appState, { setAppBatchReportIsLoading } ] = appStateAccessor(),
      isLoadingMessage = appState.app.reports.batch.isLoadingMessage;
    ReactTestUtils.act(() => setAppBatchReportIsLoading(true));
    batchReport.update();
    expect(batchReport.contains(
      <Message left={COLUMN_WIDTH} message={isLoadingMessage} />
    ));
  });

  it('loads a simple report and autoselects entries', done => {
    const batchReport = renderBatchReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/reports/123");
      request.respondWith({
        status: 200,
        response: SIMPLE_REPORT,
      }).then(() => {
        batchReport.update();
        const selection = batchReport.state("selectedUIDs");
        expect(selection.length).toBe(3);
        expect(selection).toEqual([
          "520a92e4-325e-4077-93e6-55d7091a3f83",
          "21739167-b30f-4c13-a315-ef6ae52fd1f7",
          "cb144b10-bdb0-44d3-9170-d8016dd19ee7",
        ]);
        expect(batchReport).toMatchSnapshot();
        done();
      });
    });
  });

  it('loads a more complex report and autoselects entries', done => {
    const batchReport = renderBatchReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/reports/123");
      request.respondWith({
        status: 200,
        response: TESTPLAN_REPORT,
      }).then(() => {
        batchReport.update();
        const selection = batchReport.state("selectedUIDs");
        expect(selection.length).toBe(1);
        expect(selection).toEqual(["520a92e4-325e-4077-93e6-55d7091a3f83"]);
        expect(batchReport).toMatchSnapshot();
        done();
      });
    });
  });

  it('renders an error message when Testplan report cannot be found.', done => {
    const batchReport = renderBatchReport();
    moxios.wait(function () {
      let request = moxios.requests.mostRecent();
      request.respondWith({
        status: 404,
      }).then(function () {
        batchReport.update();
        const message = batchReport.find(Message);
        const expectedMessage = 'Error: Request failed with status code 404';
        expect(message.props().message).toEqual(expectedMessage);
        done();
      })
    })
  });

});
