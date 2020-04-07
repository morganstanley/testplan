import React from 'react';
import InfoModal from './InfoModal';
import HelpModal from './HelpModal';
import TopNavbar from './TopNavbar';

/** @typedef {any|string|number|boolean|null|symbol|BigInt} ActuallyAny */
/** @typedef {keyof typeof STATUS_CATEGORY} StatusType */

/**
 * Top toolbar
 * @param {React.PropsWithChildren<{}>} props
 * @returns {React.FunctionComponentElement}
 */
export default function Toolbar({ children = null }) {
  return (
    <div>
      <TopNavbar>
        {children}
      </TopNavbar>
      <HelpModal />
      <InfoModal />
    </div>
  );
}
