/* Unit tests for the TextAttachment component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import moxios from 'moxios';

import TextAttachment from '../TextAttachment.js';

describe('TextAttachment', () => {
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

  it('displays loading spinner when mounted', () => {
    const renderedText = shallow(
      <TextAttachment
        src="/var/tmp/attachment.txt"
        file_name="attachment.txt"
      />
    );
    expect(renderedText.state("loading")).toBeTruthy();
    expect(renderedText).toMatchSnapshot();
  });

  it('renders text returned from the backend', () => {
    const text = "testplan\n".repeat(100);
    const renderedText = shallow(
      <TextAttachment
        src="/var/tmp/attachment.txt"
        file_name="attachment.txt"
      />
    );
    renderedText.instance().handleText(text);
    renderedText.update();
    expect(renderedText.state("originalText")).toBe(text + "<newline>");
    expect(renderedText).toMatchSnapshot();
  });

  it('displays error message if API request fails', done => {
    const renderedText = shallow(
      <TextAttachment
        src="/var/tmp/attachment.txt"
        file_name="attachment.txt"
      />
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      request.respondWith({
        status: 503,
        message: "Service Unavailable",
      }).then(() => {
        renderedText.update();
        expect(renderedText.state("error")).toBeTruthy();
        expect(renderedText).toMatchSnapshot();
        done();
      });
    });
  });
});

