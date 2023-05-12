import React, { useContext } from "react";
import PropTypes from "prop-types";
import { AssertionContext } from "../Common/context";
import { EXPAND_STATUS } from "../Common/defaults";
import Assertion from "./Assertion";
import { ErrorBoundary } from '../Common/ErrorBoundary';

/**
 * A component that wraps the rendered assertions. It is also the point where
 * recursion begins for grouped assertions.
 */
const AssertionGroup = (props) => {
  const assertionStatus = useContext(AssertionContext);

  return props.entries
    .filter((assertion) => {
      if (props.filter === "pass") {
        // Log assertion will be displayed
        if (assertion.passed === false) return false;
      } else if (props.filter === "fail") {
        // Log assertion will be displayed
        if (assertion.passed === true) return false;
      }
      return true;
    })
    .map((assertion, index) => {
      // Determine expand status for one assertion
      let expand;
      const assertionKey = `${props.assertionGroupUid}_${index}`;
      if (
        typeof assertionStatus.assertions[assertionKey] !== "undefined" &&
        assertionStatus.assertions[assertionKey].time >
          assertionStatus.globalExpand.time
      ) {
        expand = assertionStatus.assertions[assertionKey].status;
      } else {
        if (assertionStatus.globalExpand.status !== EXPAND_STATUS.DEFAULT) {
          expand = assertionStatus.globalExpand.status;
        } else {
          expand =
            assertion.passed === false
              ? EXPAND_STATUS.EXPAND
              : EXPAND_STATUS.COLLAPSE;
        }
      }

      return (
        <ErrorBoundary>
          <Assertion
            key={assertionKey}
            uid={assertionKey}
            assertion={assertion}
            expand={expand}
            toggleExpand={() => {
              assertionStatus.updateAssertionStatus(
                [assertionKey],
                expand === EXPAND_STATUS.EXPAND
                  ? EXPAND_STATUS.COLLAPSE
                  : EXPAND_STATUS.EXPAND
              );
            }}
            index={index}
            filter={props.filter}
            displayPath={props.displayPath}
            reportUid={props.reportUid}
          />
        </ErrorBoundary>
      );
    });
};

AssertionGroup.propTypes = {
  /** Array of assertions to be rendered */
  entries: PropTypes.arrayOf(PropTypes.object),
  /** Assertion group unique id */
  assertionGroupUid: PropTypes.string,
  /** Assertion filter */
  filter: PropTypes.string,
  /** ReportUid */
  reportUid: PropTypes.string,
};

export default AssertionGroup;
