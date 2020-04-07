import React from 'react';
import NavItem from 'reactstrap/lib/NavItem';
import { css } from 'aphrodite';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faInfo } from '@fortawesome/free-solid-svg-icons';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

library.add(faInfo);

/**
 * Return the info button which toggles the info modal.
 * @returns {React.FunctionComponentElement}
 */
export default function InfoButton() {
  const [ isShowInfoModal, setShowInfoModal ] = useReportState(
    'app.reports.batch.isShowInfoModal',
    'setAppBatchReportShowInfoModal',
  );
  const onClick = evt => {
    evt.stopPropagation();
    setShowInfoModal(!isShowInfoModal);
  };
  return (
    <NavItem>
      <div className={css(navStyles.buttonsBar)}>
        <span onClick={onClick}>
          <FontAwesomeIcon key='toolbar-info'
                           className={css(navStyles.toolbarButton)}
                           icon={faInfo.iconName}
                           title='Info'
          />
        </span>
      </div>
    </NavItem>
  );
}
