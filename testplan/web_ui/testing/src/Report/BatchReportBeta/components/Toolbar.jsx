import React from 'react';
import InfoModal from './InfoModal';
import HelpModal from './HelpModal';
import TopNavbar from './TopNavbar';

export default function Toolbar({ children = null }) {
  return(
    <div>
      <TopNavbar>{children}</TopNavbar>
      <HelpModal />
      <InfoModal />
    </div>
  );
}
