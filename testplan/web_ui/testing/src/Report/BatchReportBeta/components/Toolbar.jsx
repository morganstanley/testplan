import React from 'react';
import InfoModal from './InfoModal';
import TopNavbar from './TopNavbar';

export default function Toolbar({ children = null }) {
  return(
    <div>
      <TopNavbar>{children}</TopNavbar>
      <InfoModal />
    </div>
  );
}
