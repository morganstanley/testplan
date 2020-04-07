import React from 'react';
import NavItem from 'reactstrap/lib/NavItem';
import { css } from 'aphrodite';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPrint } from '@fortawesome/free-solid-svg-icons';
import { library } from '@fortawesome/fontawesome-svg-core';

import navStyles from '../../../Toolbar/navStyles';

library.add(faPrint);

/**
 * Return the button which prints the current testplan.
 * @returns {React.FunctionComponentElement}
 */
export default () => (
  <NavItem>
    <div className={css(navStyles.buttonsBar)}>
      <span onClick={window.print}>
        <FontAwesomeIcon key='toolbar-print'
                         className={css(navStyles.toolbarButton)}
                         icon={faPrint.iconName}
                         title='Print page'
        />
      </span>
    </div>
  </NavItem>
);
