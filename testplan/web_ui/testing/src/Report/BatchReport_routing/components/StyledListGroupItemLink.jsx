import React from 'react';
import ListGroupItem from 'reactstrap/lib/ListGroupItem';
import { css } from 'aphrodite';

import StyledNavLink from './StyledNavLink';
import { navUtilsStyles } from '../style';

const StyledListGroupItemLink = ({ pathname, dataUid, ...props }) => (
  <ListGroupItem {...props}
                 tag={StyledNavLink}
                 pathname={pathname}
                 dataUid={dataUid}
                 className={css(
                   navUtilsStyles.navButton,
                   navUtilsStyles.navButtonInteract,
                 )}
  />
);
StyledListGroupItemLink.propTypes = StyledNavLink.propTypes;

export default StyledListGroupItemLink;
