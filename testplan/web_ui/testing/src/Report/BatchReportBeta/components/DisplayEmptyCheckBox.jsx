import React from 'react';
import { Label, Input, DropdownItem } from 'reactstrap';
import { css } from 'aphrodite';
import { connect } from 'react-redux';
import { mkGetUIIsDisplayEmpty } from '../state/uiSelectors';
import { setDisplayEmpty } from '../state/uiActions';
import navStyles from '../../../Toolbar/navStyles';

const DROPDOWN_ITEM_CLASSES = css(navStyles.dropdownItem);
const FILTER_LABEL_CLASSES = css(navStyles.filterLabel);

const connector = connect(
  () => {
    const getIsDisplayEmpty = mkGetUIIsDisplayEmpty();
    return function mapStateToProps(state) {
      return {
        isDisplayEmpty: getIsDisplayEmpty(state),
      };
    };
  },
  function mapDispatchToProps(dispatch) {
    return {
      boundSetDisplayEmpty: isDisplay => dispatch(setDisplayEmpty(isDisplay)),
    };
  },
  function mergeProps(stateProps, dispatchProps, ownProps) {
    const { isDisplayEmpty } = stateProps;
    const { boundSetDisplayEmpty } = dispatchProps;
    const { label } = ownProps;
    return {
      label: label || '',
      isDisplayEmpty,
      onChange: () => boundSetDisplayEmpty(!isDisplayEmpty),
    };
  }
);

const DisplayEmptyCheckBox = ({ label, isDisplayEmpty, onChange }) => (
  <DropdownItem toggle={false} className={DROPDOWN_ITEM_CLASSES}>
    <Label check className={FILTER_LABEL_CLASSES}>
      <Input type='checkbox'
             name='displayEmpty'
             checked={!isDisplayEmpty}
             onChange={onChange}
      />
      {' ' + label}
    </Label>
  </DropdownItem>
);

export default connector(DisplayEmptyCheckBox);
