/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import PrintButton from '../PrintButton';
import { render } from 'enzyme';
import { StyleSheetTestUtils } from 'aphrodite';

describe('PrintButton', () => {
  beforeEach(() => StyleSheetTestUtils.suppressStyleInjection());
  afterEach(() => StyleSheetTestUtils.clearBufferAndResumeStyleInjection());
  it('renders correctly', () => {
    // using 'render' since this component takes no children
    expect(render(<PrintButton/>)).toMatchSnapshot();
  });
  // TODO: add test that clicks on the button and checks that the user is
  //  prompted to print once puppeteer is setup
  it.todo('prompts user to print');
});
