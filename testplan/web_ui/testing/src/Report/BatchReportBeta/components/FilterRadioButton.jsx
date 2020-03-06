import React from 'react';
import { DropdownItem, Input, Label } from 'reactstrap';
import { connect } from 'react-redux';
import { mkGetUIFilter } from '../state/uiSelectors';
import { setFilter } from '../state/uiActions';
import { DROPDOWN_ITEM_CLASSES, FILTER_LABEL_CLASSES } from '../styles';

const connector = connect(
  () => {
    const getFilter = mkGetUIFilter();
    return function mapStateToProps(state) {
      return {
        filter: getFilter(state),
      };
    };
  },
  function mapDispatchToProps(dispatch) {
    return {
      onChange: evt => {
        dispatch(setFilter(evt.currentTarget.value));
      },
    };
  },
  function mergeProps(stateProps, dispatchProps, ownProps) {
    const { filter } = stateProps;
    const { onChange } = dispatchProps;
    const { value, label } = ownProps;
    return {
      value,
      label,
      isChecked: filter === value,
      onChange,
    };
  },
);

const FilterRadioButton = ({ isChecked, onChange, value, label }) => (
  <DropdownItem toggle={false} className={DROPDOWN_ITEM_CLASSES}>
    <Label check className={FILTER_LABEL_CLASSES}>
      <Input type='radio'
             name='filter'
             value={value}
             checked={isChecked}
             onChange={onChange}
      />
      {' ' + label}
    </Label>
  </DropdownItem>
);

export default connector(FilterRadioButton);
