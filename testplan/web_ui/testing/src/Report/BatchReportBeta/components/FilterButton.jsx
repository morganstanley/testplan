import React from 'react';
import {
  DropdownItem,
  DropdownMenu,
  DropdownToggle,
  UncontrolledDropdown,
} from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFilter } from '@fortawesome/free-solid-svg-icons';
import { library } from '@fortawesome/fontawesome-svg-core';
import {
  TOOLBAR_BUTTON_CLASSES,
  BUTTONS_BAR_CLASSES,
  FILTER_DROPDOWN_CLASSES,
} from '../styles';
import FilterRadioButton from './FilterRadioButton';
import DisplayEmptyCheckBox from './DisplayEmptyCheckBox';
import * as filterStates from '../../../Common/filterStates';

library.add(faFilter);

export default function FilterButton({ toolbarStyle }) {
  return (
    <UncontrolledDropdown nav inNavbar className={BUTTONS_BAR_CLASSES}>
      <DropdownToggle nav className={toolbarStyle}>
        <FontAwesomeIcon key='toolbar-filter'
                         className={TOOLBAR_BUTTON_CLASSES}
                         icon={faFilter.iconName}
                         title='Choose filter'
        />
      </DropdownToggle>
      <DropdownMenu className={FILTER_DROPDOWN_CLASSES}>
        <FilterRadioButton value={filterStates.ALL} label='All'/>
        <FilterRadioButton value={filterStates.FAILED} label='Failed only'/>
        <FilterRadioButton value={filterStates.PASSED} label='Passed only'/>
        <DropdownItem divider/>
        <DisplayEmptyCheckBox label='Hide empty testcase'/>
      </DropdownMenu>
    </UncontrolledDropdown>
  );
}
