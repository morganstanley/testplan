import PropTypes from "prop-types";
import { Card, CardBody, Collapse } from "reactstrap";
import { css, StyleSheet } from "aphrodite";
import { useAtomValue } from "jotai";

import { ErrorBoundary } from "../Common/ErrorBoundary";
import BasicAssertion from "./AssertionTypes/BasicAssertion";
import MarkdownAssertion from "./AssertionTypes/MarkdownAssertion";
import CodeLogAssertion from "./AssertionTypes/CodeLogAssertion";
import TableLogAssertion from "./AssertionTypes/TableAssertions/TableLogAssertion";
import TableMatchAssertion from "./AssertionTypes/TableAssertions/TableMatchAssertion";
import ColumnContainAssertion from "./AssertionTypes/TableAssertions/ColumnContainAssertion";
import DictLogAssertion from "./AssertionTypes/DictAssertions/DictLogAssertion";
import FixLogAssertion from "./AssertionTypes/DictAssertions/FixLogAssertion";
import DictMatchAssertion from "./AssertionTypes/DictAssertions/DictMatchAssertion";
import FixMatchAssertion from "./AssertionTypes/DictAssertions/FixMatchAssertion";
import NotImplementedAssertion from "./AssertionTypes/NotImplementedAssertion";
import AssertionHeader from "./AssertionHeader";
import AssertionGroup from "./AssertionGroup";
import { BASIC_ASSERTION_TYPES } from "../Common/defaults";
import XYGraphAssertion from "./AssertionTypes/GraphAssertions/XYGraphAssertion";
import DiscreteChartAssertion from "./AssertionTypes/GraphAssertions/DiscreteChartAssertion";
import SummaryBaseAssertion from "./AssertionSummary";
import AttachmentAssertion from "./AssertionTypes/AttachmentAssertions";
import PlotlyAssertion from "./AssertionTypes/PlotlyAssertion";
import AttachedDirAssertion from "./AssertionTypes/AttachedDirAssertion";
import {
  RegexAssertion,
  RegexMatchLineAssertion,
} from "./AssertionTypes/RegexAssertions";
import LogfileMatchAssertion from "./AssertionTypes/LogfileMatchAssertion";
import { EXPAND_STATUS } from "../Common/defaults";
import XMLCheckAssertion from "./AssertionTypes/XMLCheckAssertion";
import { showStatusIconsPreference } from "../UserSettings/UserSettings";

/**
 * Component to render one assertion.
 */
function Assertion({
  assertion,
  displayPath,
  expand,
  filter,
  index,
  uid,
  reportUid,
  toggleExpand,
}) {
  /**
   * Get the component object of the assertion.
   * @param {String} props - Assertion type props.
   * @returns {Object|null} - Return the assertion component class if the
   * assertion is implemented.
   * @public
   */
  const assertionComponent = (assertionType) => {
    let graphAssertion;
    if (assertion.discrete_chart) {
      graphAssertion = DiscreteChartAssertion;
    } else {
      graphAssertion = XYGraphAssertion;
    }

    const assertionMap = {
      TableLog: TableLogAssertion,
      TableMatch: TableMatchAssertion,
      TableDiff: TableMatchAssertion,
      ColumnContain: ColumnContainAssertion,
      DictLog: DictLogAssertion,
      DictMatch: DictMatchAssertion,
      FixLog: FixLogAssertion,
      FixMatch: FixMatchAssertion,
      Graph: graphAssertion,
      Attachment: AttachmentAssertion,
      MatPlot: AttachmentAssertion,
      Markdown: MarkdownAssertion,
      CodeLog: CodeLogAssertion,
      Plotly: PlotlyAssertion,
      Directory: AttachedDirAssertion,
      RegexMatch: RegexAssertion,
      RegexMatchNotExists: RegexAssertion,
      RegexSearch: RegexAssertion,
      RegexSearchNotExists: RegexAssertion,
      RegexFindIter: RegexAssertion,
      RegexMatchLine: RegexMatchLineAssertion,
      XMLCheck: XMLCheckAssertion,
      LogfileMatch: LogfileMatchAssertion,
    };
    if (assertionMap[assertionType]) {
      return assertionMap[assertionType];
    } else if (BASIC_ASSERTION_TYPES.indexOf(assertionType) >= 0) {
      return BasicAssertion;
    }
    return null;
  };

  let isAssertionGroup = false;
  let assertionType = assertion.type;
  switch (assertionType) {
    case "Group":
      isAssertionGroup = true;
      assertionType = (
        <AssertionGroup
          assertionGroupUid={uid}
          entries={assertion.entries}
          filter={filter}
          reportUid={reportUid}
          displayPath={displayPath}
        />
      );
      break;
    case "Summary":
      assertionType = (
        <SummaryBaseAssertion
          assertion={assertion}
          assertionGroupUid={uid}
          filter={filter}
        />
      );
      break;
    default: {
      const AssertionTypeComponent = assertionComponent(assertionType);
      if (AssertionTypeComponent) {
        assertionType = (
          <AssertionTypeComponent assertion={assertion} reportUid={reportUid} />
        );
      } else {
        assertionType = <NotImplementedAssertion />;
      }
    }
  }
  let showStatusIcons = useAtomValue(showStatusIconsPreference);

  return (
    <Card className={css(styles.card)}>
      <AssertionHeader
        assertion={assertion}
        uid={uid}
        toggleExpand={toggleExpand}
        index={index}
        displayPath={displayPath}
        showStatusIcons={showStatusIcons}
      />
      <Collapse
        isOpen={expand === EXPAND_STATUS.EXPAND}
        className={css(styles.collapseDiv)}
        style={{ paddingRight: isAssertionGroup ? null : "1.25rem" }}
      >
        <ErrorBoundary>
          <CardBody
            className={css(
              isAssertionGroup ? styles.groupCardBody : styles.assertionCardBody
            )}
          >
            {expand === EXPAND_STATUS.EXPAND ? assertionType : null}
          </CardBody>
        </ErrorBoundary>
      </Collapse>
    </Card>
  );
}

Assertion.propTypes = {
  /** Assertion to be rendered */
  assertion: PropTypes.object,
  /** Expand status of the assertion */
  expand: PropTypes.string,
  /** Expand status update function of the assertion */
  toggleExpand: PropTypes.func,
  /** Index of the assertion */
  index: PropTypes.number,
  /** Assertion filter */
  filter: PropTypes.string,
  /** Report Uid */
  reportUid: PropTypes.string,
};

const styles = StyleSheet.create({
  assertionCardBody: {
    padding: ".5rem .75rem",
    fontSize: "13px",
    fontFamily: "monospace",
  },

  groupCardBody: {
    padding: "0rem",
  },

  card: {
    margin: ".5rem 0rem .5rem .5rem",
    border: "0px",
  },

  collapseDiv: {
    paddingLeft: "1.25rem",
  },
});

export default Assertion;
