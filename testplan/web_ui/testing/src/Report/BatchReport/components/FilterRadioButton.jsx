import React from 'react';
import DropdownItem from 'reactstrap/lib/DropdownItem';
import Input from 'reactstrap/lib/Input';
import Label from 'reactstrap/lib/Label';
import { css } from 'aphrodite';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

/**
 * Buttons used to set the filters
 * @param {Object} obj
 * @param {string} obj.value
 * @param {string} obj.label
 * @returns {React.FunctionComponentElement}
 */
export default function FilterRadioButton({ value, label }) {
  const [ filter, setFilter ] = useReportState(
    'app.reports.batch.filter', 'setAppBatchReportFilter',
  );
  return (
    <DropdownItem toggle={false} className={css(navStyles.dropdownItem)}>
      <Label check className={css(navStyles.filterLabel)}>
        <Input type='radio'
               name='filter'
               value={value}
               checked={filter === value}
               onChange={evt => setFilter(evt.currentTarget.value)}
        />
        {' ' + label}
      </Label>
    </DropdownItem>
  );
}
