import { useState } from "react";
import PropTypes from "prop-types";
import { css, StyleSheet } from "aphrodite";
import { CardHeader, Tooltip } from "reactstrap";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faLayerGroup } from "@fortawesome/free-solid-svg-icons";
import Button from "@material-ui/core/Button";
import Linkify from "linkify-react";

library.add(faLayerGroup);

/**
 * Header component of an assertion.
 */
function AssertionHeader({
  assertion,
  displayPath,
  uid,
  toggleExpand,
}) {
  const [isUTCTooltipOpen, setIsUTCTooltipOpen] = useState(false);
  const [isPathTooltipOpen, setIsPathTooltipOpen] = useState(false);
  const [isDurationTooltipOpen, setIsDurationTooltipOpen] = useState(false);

  /**
   * Toggle the visibility of tooltip of file path.
   */
  const togglePathTooltip = () => {
    setIsPathTooltipOpen(!isPathTooltipOpen);
  };

  /**
   * Toggle the visibility of tooltip of assertion start time.
   */
  const toggleUTCTooltip = () => {
    setIsUTCTooltipOpen(!isUTCTooltipOpen);
  };

  /**
   * Toggle the visibility of tooltip of duration between assertions.
   */
  const toggleDurationTooltip = () => {
    setIsDurationTooltipOpen(!isDurationTooltipOpen);
  };

  const cardHeaderColorStyle =
    assertion.passed === undefined
      ? styles.cardHeaderColorLog
      : assertion.passed
      ? styles.cardHeaderColorPassed
      : styles.cardHeaderColorFailed;

  const timeInfoArray = assertion.timeInfoArray || [];
  let component =
    assertion.utc_time === undefined ? (
      <span className={css(styles.cardHeaderAlignRight)}>
        <FontAwesomeIcon // Should be a nested assertion group
          size="sm"
          key="faLayerGroup"
          icon="layer-group"
          className={css(styles.icon)}
        />
      </span>
    ) : timeInfoArray.length === 0 ? (
      <span className={css(styles.cardHeaderAlignRight)}></span>
    ) : (
      <>
        <span
          className={css(styles.cardHeaderAlignRight, styles.timeInfo)}
          id={`tooltip_duration_${timeInfoArray[0]}`}
          style={{ order: 4, display: "inline-flex", alignItems: "center" }}
        >
          {timeInfoArray[2]}
        </span>
        <span
          className={css(styles.cardHeaderAlignRight)}
          style={{ order: 3 }}
        >
          &nbsp;&nbsp;
        </span>
        <span
          className={css(styles.cardHeaderAlignRight, styles.timeInfo)}
          id={`tooltip_utc_${timeInfoArray[0]}`}
          style={{ order: 6, display: "inline-flex", alignItems: "center" }}
        >
          {timeInfoArray[1]}
        </span>
        <span
          className={css(styles.cardHeaderAlignRight)}
          style={{ order: 5 }}
        >
          &nbsp;&nbsp;
        </span>
        <Tooltip
          placement="bottom"
          isOpen={isUTCTooltipOpen}
          target={`tooltip_utc_${timeInfoArray[0]}`}
          toggle={toggleUTCTooltip}
        >
          {"Assertion start time"}
        </Tooltip>
        <Tooltip
          placement="bottom"
          isOpen={isDurationTooltipOpen}
          target={`tooltip_duration_${timeInfoArray[0]}`}
          toggle={toggleDurationTooltip}
        >
          {"Time elapsed since last assertion"}
        </Tooltip>
      </>
    );

  let pathButton = displayPath ? (
    <>
      <Button
        size="small"
        className={css(styles.cardHeaderAlignRight, styles.timeInfo)}
        onClick={() => {
          navigator.clipboard.writeText(getPath(assertion));
        }}
        style={{ order: 2, marginLeft: "10px" }}
      >
        <span
          id={`tooltip_path_${uid}`}
          className={css(cardHeaderColorStyle)}
        >
          {renderPath(assertion)}
        </span>
      </Button>
      <Tooltip
        isOpen={isPathTooltipOpen}
        target={`tooltip_path_${uid}`}
        toggle={togglePathTooltip}
      >
        {getPath(assertion)}
      </Tooltip>
    </>
  ) : (
    <></>
  );

  const description = assertion.description ? (
    assertion.type === "Log" ? (
      <Linkify
        options={{
          target: "_blank",
          validate: {
            url: (value) => /^https?:\/\//.test(value),
          },
        }}
      >
        {assertion.description}
      </Linkify>
    ) : (
      assertion.description + " "
    )
  ) : (
    ""
  );

  return (
    <CardHeader className={css(styles.cardHeader, cardHeaderColorStyle)}>
      <div style={{ display: "flex" }}>
        <span
          className={css(styles.button)}
          onClick={toggleExpand}
          style={{
            order: 1,
            flexGrow: 4,
            padding: ".125rem 0.75rem",
            ...assertion.custom_style,
          }}
        >
          <span style={{ fontWeight: "bold" }}>{description}</span>
          <span>({assertion.type})</span>
        </span>

        {component}
        {pathButton}
        {/*
          TODO will be implemented when complete permalink feature
          linkIcon
        */}
      </div>
    </CardHeader>
  );
}

AssertionHeader.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
  /** Index of the assertion */
  index: PropTypes.number,
  /** Function when clicking header */
  onClick: PropTypes.func,
};

const renderPath = (assertion) => {
  if (assertion.file_path && assertion.line_no) {
    return (
      <>
        <span className={css(styles.icon)}>
          <i class="fa fa-copy fa-s"></i>
        </span>
        <div className={css(styles.cardHeaderPath)}>{getPath(assertion)}</div>
      </>
    );
  }
  return null;
};

const getPath = (assertion) => {
  if (assertion.file_path && assertion.line_no) {
    return assertion.file_path + ":" + assertion.line_no;
  }
  return null;
};

const styles = StyleSheet.create({
  cardHeader: {
    padding: "0",
    fontSize: "small",
    lineHeight: 1.75,
    backgroundColor: "rgba(0,0,0,0)", // Move to defaults?
    borderBottom: "1px solid",
  },

  button: {
    cursor: "pointer",
  },

  cardHeaderColorLog: {
    borderBottomColor: "#000000", // Move to defaults?
    color: "#000000", // Move to defaults?
  },

  cardHeaderColorPassed: {
    borderBottomColor: "#28a745", // Move to defaults
    color: "#28a745", // Move to defaults
  },

  cardHeaderColorFailed: {
    borderBottomColor: "#dc3545", // Move to defaults
    color: "#dc3545", // Move to defaults
  },

  cardHeaderAlignRight: {
    float: "right",
  },

  timeInfo: {
    padding: "4px 0px",
    fontFamily: "Roboto, Helvetica, Arial, sans-serif",
  },

  cardHeaderPath: {
    float: "right",
    fontSize: "small",
    maxWidth: "400px",
    "-webkit-line-clamp": 1,
    "-webkit-box-orient": "vertical",
    "white-space": "nowrap",
    direction: "rtl",
    overflow: "hidden",
    textOverflow: "ellipsis",
    textTransform: "none",
  },

  collapseDiv: {
    paddingLeft: "1.25rem",
  },

  icon: {
    margin: "0rem .25rem 0rem 0rem",
  },
});

export default AssertionHeader;
