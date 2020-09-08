import React from 'react';
import { NavItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPrint } from '@fortawesome/free-solid-svg-icons';
import { library } from '@fortawesome/fontawesome-svg-core';
import { TOOLBAR_BUTTON_CLASSES, BUTTONS_BAR_CLASSES } from '../styles';

library.add(faPrint);

export default function PrintButton() {
  return(
    <NavItem className={BUTTONS_BAR_CLASSES}>
      <FontAwesomeIcon key='toolbar-print'
                       className={TOOLBAR_BUTTON_CLASSES}
                       icon={faPrint.iconName}
                       title='Print page'
                       onClick={window.print}
      />
    </NavItem>
  );
};
