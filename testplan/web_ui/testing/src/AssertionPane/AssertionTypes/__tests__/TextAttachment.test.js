/* Unit tests for the TextAttachment component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import moxios from 'moxios';
import {CardContent} from "@material-ui/core"
import SyntaxHighlighter from "react-syntax-highlighter"

import TextAttachment from '../TextAttachment';
import AttachmentAssertionCardHeader from '../AttachmentAssertionCardHeader';

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

  it('renders text returned from the backend', done => {
    const text = "testplan\n".repeat(100);
    const src = "/var/tmp/attachment.txt";
    const renderedText = shallow(
      <TextAttachment
        src={src}
        file_name="attachment.txt"
      />
    );

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();      
      const line = "Test line\n"
      request.respondWith({
        status: 200,
        response: line.repeat(53),
      }).then(() => {
        renderedText.update();
        const highlighter = renderedText.find(SyntaxHighlighter)
        expect(highlighter.first().props().children).toEqual("...\n" + line.repeat(19) + "<newline>")
        expect(renderedText.find(AttachmentAssertionCardHeader).first().props().src).toBe(src)
        expect(renderedText).toMatchSnapshot();
        done();
      });
    },100);
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
        response: "Service Unavailable",
      }).then(() => {
        renderedText.update();
        const content = renderedText.find(CardContent);
        expect(content).toHaveLength(1);
        expect(content.text()).toEqual("Service Unavailable");
        expect(renderedText).toMatchSnapshot();
        done();
      });
    },100);
  });
});

