import React from 'react';
import DropdownItem from 'reactstrap/lib/DropdownItem';
import Input from 'reactstrap/lib/Input';
import Label from 'reactstrap/lib/Label';
import { css } from 'aphrodite';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

/**
 * Buttons used to set the filters. The placeholders "<none>" are meant to alert
 * the user / developer to an omission that should be fixed.
 * @param {Object} obj
 * @param {string} [obj.value="<none>"]
 * @param {string} [obj.label="<none>"]
 * @returns {React.FunctionComponentElement}
 */
export default ({ value = '<none>', label = '<none>' }) => {
  const [ filter, setFilter ] = useReportState(
    'app.reports.batch.filter',
    'setAppBatchReportFilter',
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
};
