import React from 'react';
import PropTypes from 'prop-types';
import useReportState from '../hooks/useReportState';
import { NavLink, useLocation } from 'react-router-dom';
import { css } from 'aphrodite';
import { navUtilsStyles } from '../style';

export default function StyledNavLink({
  style = { textDecoration: 'none', color: 'currentColor' },
  isActive = () => false,  // this just makes it look better by default
  pathname, dataUid, ...props
}) {
  const [ selectedTestCase ] =
    useReportState('app.reports.batch.selectedTestCase');
  // ensure links always include the current query params
  const { search } = useLocation();
  // remove repeating slashes
  const normPathname = pathname.replace(/\/{2,}/g, '/');
  const to = { search, pathname: normPathname };
  return (
    <NavLink style={style}
             data-uid={dataUid}
             isActive={() =>
               !!selectedTestCase &&
               !!(selectedTestCase.uid) &&
               selectedTestCase.uid === dataUid
             }
             activeClassName={css(navUtilsStyles.navButtonInteract)}
             to={to}
             {...props}
    />
  );
};
StyledNavLink.propTypes = {
  pathname: PropTypes.string.isRequired,
  dataUid: PropTypes.string.isRequired,
  style: PropTypes.object,
  isActive: PropTypes.func,
};
