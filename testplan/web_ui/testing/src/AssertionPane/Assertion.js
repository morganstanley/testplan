import PropTypes from "prop-types";
import { Card, CardBody, Collapse } from "reactstrap";
import { css, StyleSheet } from "aphrodite";
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
import { EXPAND_STATUS } from "../Common/defaults";
import XMLCheckAssertion from "./AssertionTypes/XMLCheckAssertion";

/**
 * Component to render one assertion.
 */
function Assertion(props) {
  /**
   * Get the component object of the assertion.
   * @param {String} props - Assertion type props.
   * @returns {Object|null} - Return the assertion component class if the
   * assertion is implemented.
   * @public
   */
  const assertionComponent = (assertionType) => {
    let graphAssertion;
    if (props.assertion.discrete_chart) {
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
    };
    if (assertionMap[assertionType]) {
      return assertionMap[assertionType];
    } else if (BASIC_ASSERTION_TYPES.indexOf(assertionType) >= 0) {
      return BasicAssertion;
    }
    return null;
  };

  let isAssertionGroup = false;
  let assertionType = props.assertion.type;
  switch (assertionType) {
    case "Group":
      isAssertionGroup = true;
      assertionType = (
        <AssertionGroup
          assertionGroupUid={props.uid}
          entries={props.assertion.entries}
          filter={props.filter}
          reportUid={props.reportUid}
          displayPath={props.displayPath}
        />
      );
      break;
    case "Summary":
      assertionType = (
        <SummaryBaseAssertion
          assertion={props.assertion}
          assertionGroupUid={props.uid}
          filter={props.filter}
        />
      );
      break;
    default: {
      const AssertionTypeComponent = assertionComponent(assertionType);
      if (AssertionTypeComponent) {
        assertionType = (
          <AssertionTypeComponent
            assertion={props.assertion}
            reportUid={props.reportUid}
          />
        );
      } else {
        assertionType = <NotImplementedAssertion />;
      }
    }
  };

  return (
    <Card className={css(styles.card)}>
      <AssertionHeader
        assertion={props.assertion}
        uid={props.uid}
        toggleExpand={props.toggleExpand}
        index={props.index}
        displayPath={props.displayPath}
      />
      <Collapse
        isOpen={props.expand === EXPAND_STATUS.EXPAND}
        className={css(styles.collapseDiv)}
        style={{ paddingRight: isAssertionGroup ? null : "1.25rem" }}
      >
        <ErrorBoundary>
          <CardBody
            className={css(
              isAssertionGroup
                ? styles.groupCardBody
                : styles.assertionCardBody
            )}
          >
            {props.expand === EXPAND_STATUS.EXPAND
              ? assertionType
              : null}
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
