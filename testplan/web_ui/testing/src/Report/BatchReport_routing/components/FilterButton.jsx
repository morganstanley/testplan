import React from 'react';
import DropdownItem from 'reactstrap/lib/DropdownItem';
import DropdownMenu from 'reactstrap/lib/DropdownMenu';
import DropdownToggle from 'reactstrap/lib/DropdownToggle';
import UncontrolledDropdown from 'reactstrap/lib/UncontrolledDropdown';
import { css } from 'aphrodite';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFilter } from '@fortawesome/free-solid-svg-icons';
import { library } from '@fortawesome/fontawesome-svg-core';

import navStyles from '../../../Toolbar/navStyles';
import FilterRadioButton from './FilterRadioButton';
import DisplayEmptyCheckBox from './DisplayEmptyCheckBox';
import * as filterStates from '../utils/filterStates';

library.add(faFilter);

/**
 * Return the filter button which opens a drop-down menu.
 * @param {React.PropsWithoutRef<{toolbarStyle: string}>} props
 * @returns {React.FunctionComponentElement}
 */
export default ({ toolbarStyle }) => (
  <UncontrolledDropdown nav inNavbar>
    <div className={css(navStyles.buttonsBar)}>
      <DropdownToggle nav className={toolbarStyle}>
        <FontAwesomeIcon key='toolbar-filter'
                         icon={faFilter.iconName}
                         title='Choose filter'
                         className={css(navStyles.toolbarButton)}
        />
      </DropdownToggle>
    </div>
    <DropdownMenu className={css(navStyles.filterDropdown)}>
      <FilterRadioButton value={filterStates.ALL} label='All'/>
      <FilterRadioButton value={filterStates.FAILED} label='Failed only'/>
      <FilterRadioButton value={filterStates.PASSED} label='Passed only'/>
      <DropdownItem divider/>
      <DisplayEmptyCheckBox label='Hide empty testcase'/>
    </DropdownMenu>
  </UncontrolledDropdown>
);
