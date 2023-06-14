import React from "react";
import PropTypes from "prop-types";
import { css, StyleSheet } from "aphrodite";

import DescriptionPane from "./DescriptionPane";
import AssertionGroup from "./AssertionGroup";
import LogGroup from "./LogGroup";
import { useAtomValue } from "jotai";
import { displayPathPreference } from "../UserSettings/UserSettings";

/**
 * Render the assertions of the selected test case.
 */
const AssertionPane = (props) => {
  const displayPath = useAtomValue(displayPathPreference);

  let assertionPaneStyle = {
    paddingLeft: "20px",
    flex: "1",
    overflowY: "auto",
  };

  if (
    props.assertions.length !== 0 ||
    props.logs.length !== 0 ||
    props.descriptionEntries.length !== 0
  ) {
    return (
      <div style={assertionPaneStyle}>
        <div className={css(styles.infiniteScrollDiv)}>
          <DescriptionPane descriptionEntries={props.descriptionEntries} />
          <AssertionGroup
            entries={props.assertions}
            filter={props.filter}
            displayPath={displayPath}
            assertionGroupUid={props.testcaseUid}
            reportUid={props.reportUid}
          />
          <LogGroup logs={props.logs} />
        </div>
      </div>
    );
  } else {
    return null;
  }
};

AssertionPane.propTypes = {
  /** List of assertions to be rendered */
  assertions: PropTypes.arrayOf(PropTypes.object),
  /** List of error log to be rendered */
  logs: PropTypes.arrayOf(PropTypes.object),
  /** Unique identifier of the test case */
  testcaseUid: PropTypes.string,
  /** Left positional value */
  left: PropTypes.string,
  /** Assertion filter */
  filter: PropTypes.string,
  /** Report UID */
  reportUid: PropTypes.string,
  /** Selected entries' description list to be displayed */
  descriptionEntries: PropTypes.arrayOf(PropTypes.string),
};

const styles = StyleSheet.create({
  icon: {
    margin: "0rem .75rem 0rem 0rem",
    cursor: "pointer",
  },

  infiniteScrollDiv: {
    height: "calc(100% - 1.5em)",
    overflow: "scroll",
    paddingRight: "4rem",
    "::-webkit-scrollbar": {
      width: "6px",
    },
    "::-webkit-scrollbar-thumb": {
      backgroundColor: "rgba(0, 0, 0, 0.2)",
      borderRadius: "3px",
    },
    "::-webkit-scrollbar-thumb:hover": {
      backgroundColor: "rgba(0, 0, 0, 0.4)",
    },
  },

  buttonsDiv: {
    position: "absolute",
    top: "0em",
    width: "100%",
    textAlign: "right",
  },
});

export default AssertionPane;
