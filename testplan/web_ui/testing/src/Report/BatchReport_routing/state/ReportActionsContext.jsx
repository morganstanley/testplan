import React from 'react';

import reducer from './reducer';
import actionCreators from './actionCreators';
import { getChangedBitsCalculator, makeMaskMap } from '../utils';

export const actionsMaskMap = makeMaskMap(actionCreators);

export default Object.defineProperty(
  React.createContext(reducer, getChangedBitsCalculator(actionsMaskMap)),
  'displayName',
  {
    value: 'ReportActionsContext',
    writable: false,
  }
);
