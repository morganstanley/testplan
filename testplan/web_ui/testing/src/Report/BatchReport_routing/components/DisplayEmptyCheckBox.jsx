import React from 'react';
import Label from 'reactstrap/lib/Label';
import Input from 'reactstrap/lib/Input';
import DropdownItem from 'reactstrap/lib/DropdownItem';
import { css } from 'aphrodite';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

/**
 * Checkbox that determines whether empty testcases are shown
 * @param {React.PropsWithoutRef<{label: string}>} props
 * @returns {React.FunctionComponentElement}
 */
export default function DisplayEmptyCheckBox({ label = '' }) {
  const [ isDisplayEmpty, setDisplayEmpty ] = useReportState(
    'app.reports.batch.isDisplayEmpty',
    'setAppBatchReportIsDisplayEmpty',
  );
  return (
    <DropdownItem toggle={false} className={css(navStyles.dropdownItem)}>
      <Label check className={css(navStyles.filterLabel)}>
        <Input type='checkbox'
               name='displayEmpty'
               checked={!isDisplayEmpty}
               onChange={() => setDisplayEmpty(!isDisplayEmpty)}
        />
        {' ' + label}
      </Label>
    </DropdownItem>
  );
}
