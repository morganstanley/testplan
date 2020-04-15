/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import Toolbar from '../Toolbar';
import { shallow } from 'enzyme';

describe('Toolbar', () => {
  it('renders correctly', () => {
    expect(shallow(<Toolbar/>)).toMatchSnapshot();
  });
});
