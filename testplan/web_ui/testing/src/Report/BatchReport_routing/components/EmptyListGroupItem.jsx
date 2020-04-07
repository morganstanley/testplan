import React from 'react';
import ListGroupItem from 'reactstrap/lib/ListGroupItem';
import { css } from 'aphrodite';

import { navUtilsStyles } from '../style';

export default () => (
  <ListGroupItem className={css(navUtilsStyles.navButton)}>
    No entries to display...
  </ListGroupItem>
);
