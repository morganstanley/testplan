/**
 * This component is essentially a copy-paste of
 * react-router-dom/modules/HashRouter.js except the `history` component is
 * exportable independent of the Router itself. This is needed in order to
 * manipulate the hash history in our state module.
 */
import React from 'react';
import { Router, HashRouter } from 'react-router-dom';
import { createHashHistory } from 'history';

export const uiHistory = createHashHistory({ basename: '/' });
export default function UIRouter({ children = null }) {
  return (
    <Router history={uiHistory} children={children} />
  );
}
// @ts-ignore
UIRouter.propTypes = HashRouter.propTypes;
