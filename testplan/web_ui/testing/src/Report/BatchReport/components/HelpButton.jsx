import React from 'react';
import NavItem from 'reactstrap/lib/NavItem';
import { css } from 'aphrodite';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faQuestionCircle } from '@fortawesome/free-solid-svg-icons';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

library.add(faQuestionCircle);

/**
 * Return the button which toggles the help modal.
 * @returns {React.FunctionComponentElement}
 */
export default function HelpButton() {
  const [ isShowHelpModal, setShowHelpModal ] = useReportState(
    'app.reports.batch.isShowHelpModal',
    'setAppBatchReportShowHelpModal',
  );
  return React.useMemo(() => (
    <NavItem>
      <div className={css(navStyles.buttonsBar)}>
        <span onClick={() => setShowHelpModal(!isShowHelpModal)}>
          <FontAwesomeIcon key='toolbar-question'
                           className={css(navStyles.toolbarButton)}
                           icon={faQuestionCircle.iconName}
                           title='Help'
          />
        </span>
      </div>
    </NavItem>
  ), [ isShowHelpModal, setShowHelpModal ]);
}
