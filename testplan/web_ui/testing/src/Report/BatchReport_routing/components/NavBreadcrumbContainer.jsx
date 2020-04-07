import React from 'react';
import { css } from 'aphrodite';

import { navBreadcrumbStyles } from '../style';

export default ({ children }) => (
  <div className={css(navBreadcrumbStyles.navBreadcrumbs)}>
    <ul className={css(navBreadcrumbStyles.breadcrumbContainer)}>
      {children}
    </ul>
  </div>
);
