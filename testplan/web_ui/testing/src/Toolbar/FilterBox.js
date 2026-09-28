import React, { Component, createRef } from "react";
import PropTypes from "prop-types";
import { StyleSheet, css } from "aphrodite";
import { DebounceInput } from "react-debounce-input";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faSearch,
  faExclamationCircle,
  faQuestionCircle,
  faSearchPlus,
} from "@fortawesome/free-solid-svg-icons";
import SearchFieldParser from "../Parser/SearchFieldParser";
import ExtendedSearchDropdown from "./ExtendedSearchDropdown";
import { RED } from "../Common/defaults";
import { Popover, PopoverHeader, PopoverBody, Table } from "reactstrap";

/**
 * Filter box, enter filter expressions to filter entries from the Nav
 * component.
 */
class FilterBox extends Component {
  constructor(props) {
    super(props);
    this.inputField = createRef();
    this.helpIcon = createRef();
    this.extendedSearchIcon = createRef();
    this.state = {
      parserError: null,
      showHelp: false,
      showExtendedSearch: false,
      // Persist Extended Search selections across open/close
      extendedSearchState: {
        selectedTest: "",
        selectedTestsuite: "",
        selectedTestcase: "",
        selectedParams: {},
        searchText: "",
      },
    };
    this.toggleHelp = this.toggleHelp.bind(this);
    this.toggleExtendedSearch = this.toggleExtendedSearch.bind(this);
    this.closeExtendedSearch = this.closeExtendedSearch.bind(this);
    this.updateExtendedSearchState = this.updateExtendedSearchState.bind(this);
    this.helpText = (
      <>
        <p>
          Just start typing in the search bar. The test items are filtered
          automatically. The current selection if available in the search are
          maintained. All searches are <b>case insensitive</b>, except
          for the regular expression search where case sensitivity is driven
          by the expression itself.
        </p>
        <p>
          You can search by <b>free text</b>, then each word will be matched
          against multitest, testsuite or testcase name as well as tags and tag
          names. For tag or tag names the match must be exact, for the rest it
          is enough that the name contains the word. If anything match it will
          be included.
        </p>
        <p>
          There are also <b>operators</b> that can be used for more advanced
          search terms. The test items matching all the specified operators will
          be filtered. The table below summarize them with examples:
        </p>
        {this.operatorsTable()}
      </>
    );
  }

  componentDidMount() {
    if (this.inputField.current) {
      this.inputField.current.firstChild.focus();
    }
  }

  toggleHelp() {
    this.setState({ showHelp: !this.state.showHelp });
  }

  toggleExtendedSearch() {
    this.setState((prev) => ({
      showExtendedSearch: !prev.showExtendedSearch,
    }));
  }

  closeExtendedSearch() {
    this.setState({ showExtendedSearch: false });
  }

  resetExtendedSearchState() {
    this.setState({
      showExtendedSearch: false,
      extendedSearchState: {
        selectedTest: "",
        selectedTestsuite: "",
        selectedTestcase: "",
        selectedParams: {},
        searchText: "",
      },
    });
  }

  componentDidUpdate(prevProps) {
    if (
      prevProps.report?.uid !== this.props.report?.uid
    ) {
      this.resetExtendedSearchState();
    }
  }

  updateExtendedSearchState(newState) {
    this.setState((prev) => ({
      extendedSearchState: {
        ...prev.extendedSearchState,
        ...newState,
      },
    }));
  }

  hasError() {
    return Boolean(this.state.parserError);
  }

  errorHighlight() {
    return this.hasError() && styles.parseErrorHighlight;
  }

  render() {
    const supportsExtendedSearch = this.props.onExtendedSearchNavigate;

    return (
      <div className={css(styles.searchBox)}>
        <span className={css(styles.searchBoxIcon)}>
          <FontAwesomeIcon key="search" icon={faSearch} title="Search" />
        </span>
        <div className={css(styles.searchBoxInner)} ref={this.inputField}>
          <DebounceInput
            className={css(styles.searchBoxInput, this.errorHighlight())}
            placeholder="Search for tests, or tags..."
            value={this.props.filterText}
            minLength={2}
            debounceTimeout={300}
            onChange={(event) => this.onFilterChange(event)}
          />
        </div>
        <span
          className={css(styles.searchBoxInfoIcon, this.errorHighlight())}
          onClick={this.toggleHelp}
          ref={this.helpIcon}
        >
          <FontAwesomeIcon
            key="toolbar-info"
            icon={this.hasError() ? faExclamationCircle : faQuestionCircle}
            title={
              (this.hasError() ? this.state.parserError + " " : "") +
              "Click for help"
            }
          />
        </span>
        <Popover
          placement="bottom"
          className={css(styles.widePopover)}
          isOpen={this.state.showHelp}
          target={this.helpIcon}
          toggle={this.toggleHelp}
          fade={false}
        >
          <PopoverHeader>How to search</PopoverHeader>
          <PopoverBody className={css(styles.scrollablePopover)}>
            {this.helpText}
          </PopoverBody>
        </Popover>
        {supportsExtendedSearch && (
          <span
            className={css(styles.searchBoxExtendedIcon)}
            onClick={this.toggleExtendedSearch}
            ref={this.extendedSearchIcon}
          >
            <FontAwesomeIcon
              key="extended-search"
              icon={faSearchPlus}
              title="Extended Search - Search by parameters"
            />
          </span>
        )}
        {this.state.showExtendedSearch && supportsExtendedSearch && (
          <ExtendedSearchDropdown
            report={this.props.report}
            onNavigate={this.props.onExtendedSearchNavigate}
            onClose={this.closeExtendedSearch}
            handleNavFilter={this.props.handleNavFilter}
            value={this.state.extendedSearchState}
            onStateChange={this.updateExtendedSearchState}
            triggerRef={this.extendedSearchIcon}
          />
        )}
      </div>
    );
  }

  onFilterChange(e) {
    let filters = null;
    try {
      filters = SearchFieldParser.parse(e.target.value);
      this.setState({ parserError: null });
      this.props.handleNavFilter({ text: e.target.value, filters });
    } catch (error) {
      this.setState({ parserError: error?.message || String(error) });
      console.log("Could not parse search string:", error);
      this.props.handleNavFilter({ text: e.target.value, filters: [] });
    }
  }

  operatorsTable() {
    const descriptions = [
      [
        <>
          Specify a regular expression
          <br />
          <small>(search for any matches)</small>
        </>,
        ["regexp", "re"],
        ["regexp:^addition.*_[0-9]+$", "r:^addition.*_[0-9]+$"],
      ],
      [
        <>
          Specify a multitest
          <br />
          <small>(search for substring)</small>
        </>,
        ["multitest:", "mt:"],
        ["multitest:mt1", "mt:mt1"],
      ],
      [
        <>
          Specify a testsuite
          <br />
          <small>(search for substring)</small>
        </>,
        ["testsuite:", "s:"],
        ["testsuite:suite2", "s:suite2"],
      ],
      [
        <>
          Specify a testcase
          <br />
          <small>(search for substring)</small>
        </>,
        ["testcase:", "c:"],
        ["testcase:case3", "c:case3"],
      ],
      [
        <>
          Specify a tag or a named tag
          <br />
          <small>(search for exact match)</small>
        </>,
        ["tag:"],
        ["tag:fast", "tag:color=blue"],
      ],
      [
        "Searching for something contains spaces or operators",
        ['" "'],
        ['mt:"Demo multitest"', 'suite:"test suite:2"'],
      ],
      ["Test items that match multiple terms", [], ["suite:server c:restart"]],
      [
        "Test items that match any of the terms",
        ["OR", "{}"],
        ["mt:mt1 OR mt:mt2", "{mt:mt1 mt:mt2}"],
      ],
      [
        <>
          Group multiple search terms of the same type together. It is the same
          as if the term would be applied several times, so all should match.
        </>,
        ["( )"],
        ["tag:(client server)"],
      ],
    ];

    const OperatorRow = ([type, syntax, examples], index) => (
      <tr key={index}>
        <td style={{ maxWidth: "250px" }}>{type}</td>
        <td>
          <p>
            {syntax.map((s, index) => (
              <span key={index}>
                <code>{s}</code>
                <br />
              </span>
            ))}
          </p>
          <p>
            {examples.map((e, index) => (
              <span key={index}>
                <b>Example: </b>
                <code>{e}</code>
                <br />
              </span>
            ))}
          </p>
        </td>
      </tr>
    );
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>What you can search by</th>
            <th>Search operator and example</th>
          </tr>
        </thead>
        <tbody>{descriptions.map(OperatorRow)}</tbody>
      </Table>
    );
  }
}

FilterBox.propTypes = {
  /** Function to handle expressions entered into the Filter box */
  handleNavFilter: PropTypes.func,
  filterText: PropTypes.string,
  /** Report object for extended search */
  report: PropTypes.object,
  /** Callback for extended search navigation, receives array of UIDs */
  onExtendedSearchNavigate: PropTypes.func,
};

const styles = StyleSheet.create({
  searchBox: {
    height: "100%",
    padding: "0.4em",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    position: "relative",
  },
  searchBoxInner: {
    flex: 1,
  },
  searchBoxIcon: {
    flexShrink: 0,
  },
  searchBoxInfoIcon: {
    flexShrink: 0,
    cursor: "pointer",
  },
  searchBoxExtendedIcon: {
    flexShrink: 0,
    cursor: "pointer",
  },
  searchBoxInput: {
    width: "100%",
    fontSize: "normal",
    outline: "none",
    border: "none",
  },
  parseErrorHighlight: {
    color: RED,
  },
  widePopover: {
    ":defined .popover": {
      width: "600px",
      maxWidth: "50vw",
    },
  },
  scrollablePopover: {
    overflowY: "auto",
    maxHeight: "80vh",
  },
});

export default FilterBox;
