/** @jest-environment jsdom */
import React from 'react';
import EmptyListGroupItem from '../EmptyListGroupItem';
import { render } from 'enzyme';
import { StyleSheetTestUtils } from 'aphrodite';

describe('EmptyListGroupItem', () => {
  beforeEach(() => StyleSheetTestUtils.suppressStyleInjection());
  afterEach(() => StyleSheetTestUtils.clearBufferAndResumeStyleInjection());
  it('renders correctly', () => {
    // using 'render' since this component takes no children
    expect(render(<EmptyListGroupItem/>)).toMatchSnapshot();
    // TODO: add test that clicks on the button and checks that the correct docs
    //  open in a separate tab once puppeteer is setup
  });
});
