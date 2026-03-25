import React, { useContext } from "react";
import PropTypes from "prop-types";
import Assertion from "../../Assertion";
import { AssertionContext } from "../../../Common/context";
import { ErrorBoundary } from "../../../Common/ErrorBoundary";
import { EXPAND_STATUS } from "../../../Common/defaults";

const MATCH_ASSERTION_TYPE = Object.freeze({
  fix: "FixMatch",
  dict: "DictMatch",
});

/**
 * Base assertion used to render dict and fix match assertions.
 */
export default function MatchAllBaseAssertion(props) {

  const assertionStatus = useContext(AssertionContext);

  const description = props.assertion.description;

  const filter = props.filter || [];
  const showPassed = filter.includes("passed");
  const showFailed = filter.some((s) => s === "failed" || s === "error");
  const matchPassFilter =
    showPassed && !showFailed
      ? (c) => c.passed !== false
      : showFailed && !showPassed
      ? (c) => c.passed !== true
      : () => true;

  return props.assertion.matches
    .filter((comparison) => matchPassFilter(comparison))
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
        type: MATCH_ASSERTION_TYPE[props.matchType],
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

MatchAllBaseAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object.isRequired,
  /** Match type */
  matchType: PropTypes.oneOf(["fix", "dict"]).isRequired,
};
