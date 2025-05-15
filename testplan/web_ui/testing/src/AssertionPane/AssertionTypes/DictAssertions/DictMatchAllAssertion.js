import React, { useContext } from "react";
import PropTypes from "prop-types";
import Assertion from "../../Assertion";
import { AssertionContext } from "../../../Common/context";
import { ErrorBoundary } from "../../../Common/ErrorBoundary";
import { EXPAND_STATUS } from "./../../../Common/defaults";

/**
 * Component that renders DictMatchAll assertion.
 *
 * The expected list of      | The actual list of dictionaries matched
 * dictionaries of the test: | to the expected ones:
 *
 * [                         | [
 *   {'foo': 12, 'bar': 22}, |   {'foo': 13, 'bar': 25},
 *   {'foo': 13, 'bar': 23}  |   {'foo': 12, 'bar': 22}
 * ]                         | ]
 *
 *
 * 1/2: expected[1] vs values[0]
 *  ______________________________________
 * | Key        | Expected   | Value      |
 * |------------|------------|------------|
 * | foo        | 13         | 13         |
 * | bar        | 23         | 25         |
 * |____________|____________|____________|
 *
 * 2/2: expected[0] vs values[1]
 *  ______________________________________
 * | Key        | Expected   | Value      |
 * |------------|------------|------------|
 * | foo        | 12         | 12         |
 * | bar        | 22         | 22         |
 * |____________|____________|____________|
 *
 * For each comparison pair, the grid consists of three columns:
 * Key, Expected and Value.
 *  - Key: a key of the dictionary. Nested objects are displayed with indented
 *    keys.
 *  - Expected: expected value for the given key.
 *  - Value: Actual value for the given key.
 *
 */

export default function DictMatchAllAssertion(props) {
  const assertionStatus = useContext(AssertionContext);

  const description = props.assertion.description;

  return props.assertion.matches
    .filter((comparison) => {
      if (props.filter === "pass") {
        // Log assertion will be displayed
        if (comparison.passed === false) return false;
      } else if (props.filter === "fail") {
        // Log assertion will be displayed
        if (comparison.passed === true) return false;
      }
      return true;
    })
    .map((match, matchIndex) => {
      // Determine expand status for one comparison
      let expand;
      const assertionKey = `${props.reportUid}_${props.index}_${matchIndex}`;
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
            match.passed === false
              ? EXPAND_STATUS.EXPAND
              : EXPAND_STATUS.COLLAPSE;
        }
      }

      const assertion = {
        type: "DictMatch",
        description: match.description,
        passed: match.passed,
        comparison: match.comparison,
        inGroup: true,
      };

      if (assertion.description.startsWith(description)) {
        assertion.description =
          assertion.description.slice(description.length + 1);
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
            index={matchIndex}
            displayPath={props.displayPath}
            reportUid={props.reportUid}
            hideType={true}
          />
        </ErrorBoundary>
      );
    });
}

DictMatchAllAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object.isRequired,
};
