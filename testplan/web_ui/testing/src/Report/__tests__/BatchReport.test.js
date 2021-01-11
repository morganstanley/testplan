import React from 'react';
import { shallow, mount } from 'enzyme';
import { StyleSheetTestUtils } from "aphrodite";
import moxios from 'moxios';
import ReactRouterEnzymeContext from "react-router-enzyme-context";

import BatchReport from '../BatchReport';
import Message from '../../Common/Message';
import { TESTPLAN_REPORT, SIMPLE_REPORT, ERROR_REPORT } from "../../Common/sampleReports";



describe('BatchReport', () => {

  const renderBatchReport = (uid = "123") => {
    // Mock the match object that would be passed down from react-router.
    // BatchReport uses this object to get the report UID.
    const routerContext = new ReactRouterEnzymeContext();
    const mockMatch = { params: { uid: uid, selection: undefined }, path: "/testplan/:uid/:selection*"};
    return  shallow(
      <BatchReport match={mockMatch} history={routerContext.props().history}/>, {
        ...routerContext.get()
    });  
  };


  const renderBatchReportFull = (uid = "123") => {
    // Mock the match object that would be passed down from react-router.
    // BatchReport uses this object to get the report UID.
    const mockMatch = { params: { uid: uid, selection: undefined }, path: "/testplan/:uid/:selection*"};
    return mount(
      <BatchReport match={mockMatch} />
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
    const batchReport = renderBatchReport("520a92e4-325e-4077-93e6-55d7091a3f83");
    batchReport.instance().setReport(TESTPLAN_REPORT);
    batchReport.update();
    expect(batchReport).toMatchSnapshot();
  });

  it('renders loading message when fetching report', () => {
    const batchReport = renderBatchReport();
    batchReport.setState({ loading: true });
    batchReport.update();
    const message = batchReport.find(Message);
    const expectedMessage = 'Fetching Testplan report...';
    expect(message.props().message).toEqual(expectedMessage);
  });

  it('renders waiting message when waiting to start fetch', () => {
    const batchReport = renderBatchReport();
    batchReport.setState({ loading: false, error: null });
    batchReport.update();
    const message = batchReport.find(Message);
    const expectedMessage = 'Waiting to fetch Testplan report...';
    expect(message.props().message).toEqual(expectedMessage);
  });

  it('loads a simple report and autoselects entries', done => {
    const batchReport = renderBatchReport("520a92e4-325e-4077-93e6-55d7091a3f83");
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83");
      request.respondWith({
        status: 200,
        response: SIMPLE_REPORT,
      }).then(() => {
        batchReport.update();
        const props = batchReport.instance().props
        expect(props.history.location.pathname).toBe("/testplan/520a92e4-325e-4077-93e6-55d7091a3f83/21739167-b30f-4c13-a315-ef6ae52fd1f7/cb144b10-bdb0-44d3-9170-d8016dd19ee7")
        batchReport.setProps(
          {
            ...props, 
            match: {
              ...props.match, 
              params: {
                  ...props.match.params,
                  selection: "21739167-b30f-4c13-a315-ef6ae52fd1f7/cb144b10-bdb0-44d3-9170-d8016dd19ee7"
                }
              }
            }
            );        
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
    const batchReport = renderBatchReport("520a92e4-325e-4077-93e6-55d7091a3f83");
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83");
      request.respondWith({
        status: 200,
        response: TESTPLAN_REPORT,
      }).then(() => {
        batchReport.update();
        const props = batchReport.instance().props
        expect(props.history.location.pathname).toBe("/testplan/520a92e4-325e-4077-93e6-55d7091a3f83")
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

  it('shallow renders the correct HTML structure when report with errors loaded', () => {
    const batchReport = renderBatchReportFull();
    batchReport.setState({ report: ERROR_REPORT });
    batchReport.update();
    expect(batchReport).toMatchSnapshot();
  });

});
