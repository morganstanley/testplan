import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Button, ButtonGroup} from 'reactstrap';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {library} from '@fortawesome/fontawesome-svg-core';
import {
  faSortAmountUp,
  faSortAmountDown,
} from '@fortawesome/free-solid-svg-icons';
import CopyButton from './../CopyButton';
import {sortFlattenedJSON, flattenedDictToDOM} from './dictAssertionUtils';
import {SORT_TYPES} from './../../../Common/defaults';
import {uniqueId} from './../../../Common/utils';

library.add(
  faSortAmountUp,
  faSortAmountDown
);


/**
 * Component that renders the buttons of table.
 * DictLog and FixLog will render sort alphabetically buttons. DictMatch and 
 * FixMatch will render sort by alphabet buttons and sort/filter by status 
 * buttons.
 * 
 * dictAssertionUtils' {@link sortFlattenedJSON} function is called to sort
 * the table data to be displayed.
 */
class DictButtonGroup extends Component {
  constructor(props) {
    super(props);

    this.uid = this.props.uid || uniqueId();

    this.state = {
      selectedSortType: this.props.defaultSortType,
      sortedData: this.props.flattenedDict,
    };

    this.buttonMap = {};
    this.buttonMap[SORT_TYPES.ALPHABETICAL] = {
      display: 
        <FontAwesomeIcon 
          size='sm' 
          key='faSortAmountDown' 
          icon='sort-amount-down'
        />,
      onClick: this.sortByChar.bind(this)
    };

    this.buttonMap[SORT_TYPES.REVERSE_ALPHABETICAL] = {
      display: 
        <FontAwesomeIcon 
          size='sm' 
          key='faSortAmountUp' 
          icon='sort-amount-up'
        />,
      onClick: this.sortByCharReverse.bind(this)
    };

    this.buttonMap[SORT_TYPES.BY_STATUS] = {
      display: 'Status',
      onClick: this.sortByStatus.bind(this)
    };

    this.buttonMap[SORT_TYPES.ONLY_FAILURES] = {
      display: 'Failures only',
      onClick: this.filterFailure.bind(this)
    };
  }

  sortByChar() {
    let sortedData = sortFlattenedJSON(
      this.props.flattenedDict, 0, false, false
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.ALPHABETICAL,
      sortedData: sortedData
    });
  }

  sortByCharReverse() {
    let sortedData = sortFlattenedJSON(
      this.props.flattenedDict, 0, true, false
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.REVERSE_ALPHABETICAL,
      sortedData: sortedData
    });
  }

  sortByStatus() {
    let sortedData = sortFlattenedJSON(
      this.props.flattenedDict, 0, false, true
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.BY_STATUS,
      sortedData: sortedData
    });
  }

  filterFailure() {
    let sortedData = this.props.flattenedDict.filter(
      line => line[2] === 'Failed'
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.ONLY_FAILURES,
      sortedData: sortedData
    });
  }


  render() {
    let buttonGroup = [];
    this.props.sortTypeList.forEach(function(sortType){
      buttonGroup.push(
        <Button
          key={this.uid+sortType}
          outline
          color='secondary'
          size='sm'
          onClick={this.buttonMap[sortType]['onClick']}
          active={this.state.selectedSortType===sortType}
        >
          {this.buttonMap[sortType]['display']}
        </Button>
      );
    }.bind(this));

    let copyButton =
      <CopyButton value={flattenedDictToDOM(this.state.sortedData)} />;

    return (
      <ButtonGroup style={{paddingBottom: '.5rem'}}>
        {buttonGroup}{copyButton}
      </ButtonGroup>
    );
  }
}

DictButtonGroup.propTypes = {
  /** Types of button should be rendered.  */
  sortTypeList: PropTypes.arrayOf(
    PropTypes.number
  ),
  /** Function to update the sort state if sort type changed */
  setRowData: PropTypes.func.isRequired,
  /** Default type of sort button */
  defaultSortType: PropTypes.number,
  /** The data will be sorted */
  flattenedDict: PropTypes.array,
  /** unique id */
  uid: PropTypes.string,
};


export default DictButtonGroup;