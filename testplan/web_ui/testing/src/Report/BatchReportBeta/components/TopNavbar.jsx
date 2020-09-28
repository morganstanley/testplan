import React from 'react';
import { Navbar, Nav, Collapse } from 'reactstrap';
import { connect } from 'react-redux';
import { mkGetUIToolbarStyle, getSideBarWidth } from '../state/uiSelectors';
import { TOOLBAR_CLASSES, FILTER_BOX_CLASSES } from '../styles';
import FilterBoxPlaceholder from '../../../Toolbar/FilterBoxPlaceholder';
import InfoButton from './InfoButton';
import FilterButton from './FilterButton';
import PrintButton from './PrintButton';
import TagsButton from './TagsButton';
import DocumentationButton from './DocumentationButton';

const connector = connect(
  () => {
    const getToolbarStyle = mkGetUIToolbarStyle();
    return function mapStateToProps(state) {
      return {
        toolbarStyle: getToolbarStyle(state),
        sideBarWidth: getSideBarWidth(state),
      };
    };
  }
);

const TopNavbar = ({ toolbarStyle, children = null, sideBarWidth}) => (
  <Navbar light expand='md' className={TOOLBAR_CLASSES}>
    <div className={FILTER_BOX_CLASSES} style={{width: sideBarWidth}}>
      <FilterBoxPlaceholder/>
    </div>
    <Collapse navbar className={toolbarStyle}>
      <Nav navbar className='ml-auto'>
        {children}
        <InfoButton/>
        <FilterButton toolbarStyle={toolbarStyle}/>
        <PrintButton/>
        <TagsButton/>
        <DocumentationButton/>
      </Nav>
    </Collapse>
  </Navbar>
);

export default connector(TopNavbar);
