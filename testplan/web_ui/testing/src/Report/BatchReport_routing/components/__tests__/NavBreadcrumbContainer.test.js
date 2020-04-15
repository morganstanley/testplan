/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render } from '@testing-library/react';
import { StyleSheetTestUtils } from 'aphrodite';
import NavBreadcrumbContainer from '../NavBreadcrumbContainer';

describe('NavBreadcrumbContainer', () => {

  beforeEach(() => {
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it('renders correctly with dummy child', () => {
    expect(render(
      <NavBreadcrumbContainer>
        <li>Dummy LI element</li>
      </NavBreadcrumbContainer>
    ).container).toMatchSnapshot();
  });

  it('renders correctly without children', () => {
    expect(render(<NavBreadcrumbContainer/>).container).toMatchSnapshot();
  });

});
