/**
 * Components to render attached files in the UI.
 */
import React from "react";
import { css, StyleSheet } from "aphrodite";
import { withStyles } from "@material-ui/core/styles";
import MuiAccordion from "@material-ui/core/Accordion";
import MuiAccordionSummary from "@material-ui/core/AccordionSummary";
import MuiAccordionDetails from "@material-ui/core/AccordionDetails";
import Typography from "@material-ui/core/Typography";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";

import { getAttachmentUrl } from "../../Common/utils";

const Accordion = withStyles({
  root: {
    borderUp: 0,
    borderBottom: "1px solid rgba(0, 0, 0, .125)",
    borderLeft: "1px solid rgba(0, 0, 0, .125)",
    borderRight: "1px solid rgba(0, 0, 0, .125)",
    "&:not(:last-child)": {
      borderBottom: 0,
    },
    "&:before": {
      display: "none",
    },
    "&$expanded": {
      margin: "auto",
    },
  },
  expanded: {},
})(MuiAccordion);

const AccordionSummary = withStyles({
  root: {
    minHeight: 40,
    "&$expanded": {
      minHeight: 40,
    },
  },
  content: {
    margin: "12px 0",
    "&$expanded": {
      margin: "12px 0",
    },
  },
  expanded: {},
  expandIcon: {
    padding: "8px",
  },
})(MuiAccordionSummary);

const AccordionDetails = withStyles({
  root: {
    padding: "0px 16px 16px 16px",
  },
})(MuiAccordionDetails);

/**
 * Directory attachments component. Provides a direct link to download files.
 */
export const AttachedDirAssertion = (props) => {
  const num_of_files = props.assertion.file_list.length;
  return (
    <div>
      <Accordion>
        <AccordionSummary
          expandIcon={num_of_files > 0 ? <ExpandMoreIcon /> : null}
          aria-controls="panel-content"
          id="panel-header"
        >
          <Typography>
            <span className={css(styles.title)}>
              {props.assertion.source_path}
            </span>
            <br />
            <span className={css(styles.subHeader)}>
              {num_of_files + (num_of_files > 1 ? " files" : " file")}
            </span>
          </Typography>
        </AccordionSummary>
        {num_of_files > 0 ? (
          <AccordionDetails>
            <Typography>
              {getAttachedDirContent(props.assertion, props.reportUid)}
            </Typography>
          </AccordionDetails>
        ) : null}
      </Accordion>
    </div>
  );
};

/* Render the directory content in a list */
const getAttachedDirContent = (assertion, reportUid) => {
  const content = [];
  assertion.file_list.forEach((entry, index) => {
    const fileLink = getAttachmentUrl(entry, reportUid, assertion.dst_path);
    const filename = entry.split("/").pop();
    const pos = filename.lastIndexOf(".");
    const ext_name =
      pos >= 0
        ? filename.substring(pos + 1, filename.length).toLowerCase()
        : "";
    content.push(
      <span key={index} className={css(styles.textContent)}>
        {ext_name === "htm" || ext_name === "html" || ext_name === "xml" ? (
          <a href={fileLink} target="_blank" rel="noopener noreferrer">
            {entry}
          </a>
        ) : (
          <a href={fileLink} download={filename}>
            {entry}
          </a>
        )}
        <br />
      </span>
    );
  });
  return content;
};

const styles = StyleSheet.create({
  title: {
    fontSize: "large",
    color: "rgba(0, 0, 0, 0.87)",
  },
  subHeader: {
    fontSize: "medium",
    color: "rgba(0, 0, 0, 0.54)",
  },
  textContent: {
    fontSize: "small",
    padding: "0 0 0 16px",
  },
});

export default AttachedDirAssertion;
