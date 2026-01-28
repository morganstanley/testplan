import { useState } from "react";
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
function DictButtonGroup({
  defaultSortType,
  defaultFilterOptions,
  flattenedDict,
  uid,
  setRowData,
  sortTypeList,
  filterOptionList,
}) {
  const sortAndFilterData = (SortType, filterOptions) => {
    let sortedData = flattenedDict;
    if (SortType !== SORT_TYPES.NONE) {
      sortedData = sortFlattenedJSON(
        flattenedDict,
        0,
        SortType === SORT_TYPES.REVERSE_ALPHABETICAL,
        SortType === SORT_TYPES.BY_STATUS
      );
    }
    if (filterOptions.indexOf(FILTER_OPTIONS.FAILURES_ONLY) >= 0) {
      sortedData = sortedData.filter((line) => line[2] === "Failed");
    }
    if (filterOptions.indexOf(FILTER_OPTIONS.EXCLUDE_IGNORABLE) >= 0) {
      sortedData = sortedData.filter((line) => line[2] !== "Ignored");
    }
    return sortedData;
  };

  const [selectedSortType, setSelectedSortType] = useState(
    defaultSortType || SORT_TYPES.NONE
  );
  const [selectedFilterOptions, setSelectedFilterOptions] = useState(
    defaultFilterOptions || []
  );
  const [sortedData, setSortedData] = useState(
    sortAndFilterData(selectedSortType, selectedFilterOptions)
  );

  const sortBy = (sortType) => {
    const newSortedData = sortAndFilterData(sortType, selectedFilterOptions);
    setRowData(newSortedData);
    setSelectedSortType(sortType);
    setSortedData(newSortedData);
  };

  const filterBy = (filterOption) => {
    const newFilterOptions =
      selectedFilterOptions.indexOf(filterOption) >= 0
        ? selectedFilterOptions.filter((opt) => opt !== filterOption)
        : selectedFilterOptions.concat([filterOption]);
    const newSortedData = sortAndFilterData(selectedSortType, newFilterOptions);
    setRowData(newSortedData);
    setSelectedFilterOptions(newFilterOptions);
    setSortedData(newSortedData);
  };

  const buttonUid = uid || uniqueId();
  const buttonMap = {
    [SORT_TYPES.NONE]: {
      display: "Original order",
      onClick: () => sortBy(SORT_TYPES.NONE),
    },
    [SORT_TYPES.ALPHABETICAL]: {
      display: (
        <FontAwesomeIcon
          size="sm"
          key="faSortAmountDown"
          icon="sort-amount-down"
        />
      ),
      onClick: () => sortBy(SORT_TYPES.ALPHABETICAL),
    },
    [SORT_TYPES.REVERSE_ALPHABETICAL]: {
      display: (
        <FontAwesomeIcon size="sm" key="faSortAmountUp" icon="sort-amount-up" />
      ),
      onClick: () => sortBy(SORT_TYPES.REVERSE_ALPHABETICAL),
    },
    [SORT_TYPES.BY_STATUS]: {
      display: "Status",
      onClick: () => sortBy(SORT_TYPES.BY_STATUS),
    },
    [FILTER_OPTIONS.FAILURES_ONLY]: {
      display: "Failures only",
      onClick: () => filterBy(FILTER_OPTIONS.FAILURES_ONLY),
    },
    [FILTER_OPTIONS.EXCLUDE_IGNORABLE]: {
      display: "Hide ignored items",
      onClick: () => filterBy(FILTER_OPTIONS.EXCLUDE_IGNORABLE),
    },
  };

  let buttonGroup = [];

  sortTypeList.forEach((sortType) => {
    buttonGroup.push(
      <Button
        key={buttonUid + "-" + sortType.toString()}
        outline
        color="secondary"
        size="sm"
        onClick={buttonMap[sortType]["onClick"]}
        active={selectedSortType === sortType}
      >
        {buttonMap[sortType]["display"]}
      </Button>
    );
  });

  if (filterOptionList) {
    filterOptionList.forEach((filterOption) => {
      buttonGroup.push(
        <Button
          key={buttonUid + "-" + filterOption.toString()}
          outline
          color="secondary"
          size="sm"
          onClick={buttonMap[filterOption]["onClick"]}
          active={selectedFilterOptions.indexOf(filterOption) >= 0}
        >
          {buttonMap[filterOption]["display"]}
        </Button>
      );
    });
  }

  let copyButton = <CopyButton value={flattenedDictToDOM(sortedData)} />;

  return (
    <ButtonGroup style={{ paddingBottom: ".5rem" }}>
      {buttonGroup}
      {copyButton}
    </ButtonGroup>
  );
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
