import React, { Component } from "react";
import PropTypes from "prop-types";
import { Button, ButtonGroup } from "reactstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faSortAmountUp,
  faSortAmountDown,
} from "@fortawesome/free-solid-svg-icons";
import CopyButton from "./../CopyButton";
import { sortFlattenedJSON, flattenedDictToDOM } from "./dictAssertionUtils";
import { SORT_TYPES, FILTER_OPTIONS } from "./../../../Common/defaults";
import { uniqueId } from "./../../../Common/utils";

library.add(faSortAmountUp, faSortAmountDown);

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
    this.state = {
      selectedSortType: this.props.defaultSortType || SORT_TYPES.NONE,
      selectedFilterOptions: this.props.defaultFilterOptions || [],
      sortedData: this.props.flattenedDict,
    };
    this.sortAndFilterData = this.sortAndFilterData.bind(this);

    this.uid = this.props.uid || uniqueId();
    this.buttonMap = {};

    this.buttonMap[SORT_TYPES.NONE] = {
      display: "Original order",
      onClick: this.noSort.bind(this),
    };

    this.buttonMap[SORT_TYPES.ALPHABETICAL] = {
      display: (
        <FontAwesomeIcon
          size="sm"
          key="faSortAmountDown"
          icon="sort-amount-down"
        />
      ),
      onClick: this.sortByChar.bind(this),
    };

    this.buttonMap[SORT_TYPES.REVERSE_ALPHABETICAL] = {
      display: (
        <FontAwesomeIcon size="sm" key="faSortAmountUp" icon="sort-amount-up" />
      ),
      onClick: this.sortByCharReverse.bind(this),
    };

    this.buttonMap[SORT_TYPES.BY_STATUS] = {
      display: "Status",
      onClick: this.sortByStatus.bind(this),
    };

    this.buttonMap[FILTER_OPTIONS.FAILURES_ONLY] = {
      display: "Failures only",
      onClick: this.filterFailure.bind(this),
    };

    this.buttonMap[FILTER_OPTIONS.EXCLUDE_IGNORABLE] = {
      display: "Hide ignored items",
      onClick: this.filterIgnorable.bind(this),
    };
  }

  noSort() {
    let sortedData = this.props.flattenedDict;
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.NONE,
      sortedData: sortedData,
    });
  }

  sortByChar() {
    let sortedData = this.sortAndFilterData(
      SORT_TYPES.ALPHABETICAL,
      this.state.selectedFilterOptions
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.ALPHABETICAL,
      sortedData: sortedData,
    });
  }

  sortByCharReverse() {
    let sortedData = this.sortAndFilterData(
      SORT_TYPES.REVERSE_ALPHABETICAL,
      this.state.selectedFilterOptions
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.REVERSE_ALPHABETICAL,
      sortedData: sortedData,
    });
  }

  sortByStatus() {
    let sortedData = this.sortAndFilterData(
      SORT_TYPES.BY_STATUS,
      this.state.selectedFilterOptions
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedSortType: SORT_TYPES.BY_STATUS,
      sortedData: sortedData,
    });
  }

  filterFailure() {
    let filterOptions = this.state.selectedFilterOptions;
    filterOptions =
      filterOptions.indexOf(FILTER_OPTIONS.FAILURES_ONLY) >= 0
        ? filterOptions.filter((opt) => opt !== FILTER_OPTIONS.FAILURES_ONLY)
        : filterOptions.concat([FILTER_OPTIONS.FAILURES_ONLY]);
    let sortedData = this.sortAndFilterData(
      this.state.selectedSortType,
      filterOptions
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedFilterOptions: filterOptions,
      sortedData: sortedData,
    });
  }

  filterIgnorable() {
    let filterOptions = this.state.selectedFilterOptions;
    filterOptions =
      filterOptions.indexOf(FILTER_OPTIONS.EXCLUDE_IGNORABLE) >= 0
        ? filterOptions.filter(
            (opt) => opt !== FILTER_OPTIONS.EXCLUDE_IGNORABLE
          )
        : filterOptions.concat([FILTER_OPTIONS.EXCLUDE_IGNORABLE]);
    let sortedData = this.sortAndFilterData(
      this.state.selectedSortType,
      filterOptions
    );
    this.props.setRowData(sortedData);
    this.setState({
      selectedFilterOptions: filterOptions,
      sortedData: sortedData,
    });
  }

  sortAndFilterData(SortType, filterOptions) {
    let sortedData = sortFlattenedJSON(
      this.props.flattenedDict,
      0,
      SortType === SORT_TYPES.REVERSE_ALPHABETICAL,
      SortType === SORT_TYPES.BY_STATUS
    );
    if (filterOptions.indexOf(FILTER_OPTIONS.FAILURES_ONLY) >= 0) {
      sortedData = sortedData.filter((line) => line[2] === "Failed");
    }
    if (filterOptions.indexOf(FILTER_OPTIONS.EXCLUDE_IGNORABLE) >= 0) {
      sortedData = sortedData.filter((line) => line[2] !== "Ignored");
    }
    return sortedData;
  }

  render() {
    let buttonGroup = [];

    this.props.sortTypeList.forEach(
      function (sortType) {
        buttonGroup.push(
          <Button
            key={this.uid + "-" + sortType.toString()}
            outline
            color="secondary"
            size="sm"
            onClick={this.buttonMap[sortType]["onClick"]}
            active={this.state.selectedSortType === sortType}
          >
            {this.buttonMap[sortType]["display"]}
          </Button>
        );
      }.bind(this)
    );

    if (this.props.filterOptionList) {
      this.props.filterOptionList.forEach(
        function (filterOption) {
          buttonGroup.push(
            <Button
              key={this.uid + "-" + filterOption.toString()}
              outline
              color="secondary"
              size="sm"
              onClick={this.buttonMap[filterOption]["onClick"]}
              active={
                this.state.selectedFilterOptions.indexOf(filterOption) >= 0
              }
            >
              {this.buttonMap[filterOption]["display"]}
            </Button>
          );
        }.bind(this)
      );
    }

    let copyButton = (
      <CopyButton value={flattenedDictToDOM(this.state.sortedData)} />
    );

    return (
      <ButtonGroup style={{ paddingBottom: ".5rem" }}>
        {buttonGroup}
        {copyButton}
      </ButtonGroup>
    );
  }
}

DictButtonGroup.propTypes = {
  /** Button for sorting should be rendered. */
  sortTypeList: PropTypes.arrayOf(PropTypes.symbol).isRequired,
  /** Button for filtering should be rendered. */
  filterOptionList: PropTypes.arrayOf(PropTypes.symbol),
  /** Function to update the sort state if sort type changed */
  setRowData: PropTypes.func.isRequired,
  /** Default type of sort button */
  defaultSortType: PropTypes.symbol,
  /** The data will be sorted */
  flattenedDict: PropTypes.array,
  /** unique id */
  uid: PropTypes.string,
};

export default DictButtonGroup;
