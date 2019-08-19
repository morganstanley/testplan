import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import moxios from 'moxios';

import BatchReport from '../BatchReport';
import Message from '../../Common/Message';
import {TESTPLAN_REPORT} from "../../Common/sampleReports";

describe('BatchReport', () => {
  let mountedBatchReport;
  const renderBatchReport = () => {
    if (!mountedBatchReport) {
      mountedBatchReport = shallow(
        <BatchReport />
      );
    }
    return mountedBatchReport;
  };

  it('renders error message when cannot find Testplan UID', () => {
    window.location.pathname = '';
    const batchReport = renderBatchReport();
    batchReport.update();
    const message = batchReport.find(Message);
    const expectedMessage = 'Error fetching Testplan report. ' +
      '(Error retrieving UID from URL.)';
    expect(message.props().message).toEqual(expectedMessage);
  });

  describe('mock URL path', () => {

    beforeEach(() => {
      // Stop Aphrodite from injecting styles, this crashes the tests.
      StyleSheetTestUtils.suppressStyleInjection();
      mountedBatchReport = undefined;
      moxios.install();
      window.history.pushState({}, '', '/testplan/123/');
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
      const batchReport = renderBatchReport();
      batchReport.setState({report: [TESTPLAN_REPORT]});
      batchReport.update();
      expect(batchReport).toMatchSnapshot();
    });

    it('renders loading message when fetching report', () => {
      const batchReport = renderBatchReport();
      batchReport.setState({loading: true});
      batchReport.update();
      const message = batchReport.find(Message);
      const expectedMessage = 'Fetching Testplan report...';
      expect(message.props().message).toEqual(expectedMessage);
    });

    it('renders waiting message when waiting to start fetch', () => {
      const batchReport = renderBatchReport();
      batchReport.setState({loading: false, error: undefined});
      batchReport.update();
      const message = batchReport.find(Message);
      const expectedMessage = 'Waiting to fetch Testplan report...';
      expect(message.props().message).toEqual(expectedMessage);
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
          const expectedMessage = 'Error fetching Testplan report. ' +
            '(Request failed with status code 404)';
          expect(message.props().message).toEqual(expectedMessage);
          done();
        })
      })
    });

  });

  // Unsure how to test the axios request. Mocking it is easy to do
  // but we need to

});