import React, { useState, useEffect } from "react";
import { StyleSheet, css } from "aphrodite";
import axios from "axios";
import SyntaxHighlighter from "react-syntax-highlighter";
import _ from "lodash";
import {
  Card,  
  CardContent,
  Button,  
} from "@material-ui/core";
import { ExpandLess, ExpandMore} from "@material-ui/icons";
import AttachmentAssertionCardHeader from "./AttachmentAssertionCardHeader";
import { ErrorBoundary } from "../../Common/ErrorBoundary";
import { CardBody } from "reactstrap";

//Max number of lines displayed in the preview when collapsed
const DISPLAY_NUM = 20;
//Max number of lines displayed in the preview when expanded
const MAX_DISPLAY_LINE = 20000;
const MAX_DISPLAY_FILE_SIZE = 5 * 1024 * 1024; // 5 meg

function loadTextFile(url, devMode, handle, handleError) {
  if (devMode) {
    const TEST_TEXT = (
      "test1\ntest2\ntest3\ntest4\ntest5\n" + "test6".repeat(55)
    ).repeat(55);
    let text = TEST_TEXT;
    handle(text);
  } else {
    axios
      .get(url)
      .then((response) => {
        let text = response.data;
        handle(text);
      })
      .catch((error) => handleError(error));
  }
}

function getLineEnds(text) {
  let sp = -1;
  const line_ends = [];
  while (true) {
    sp = text.indexOf("\n", sp + 1);
    if (sp < 0) break;
    line_ends.push(sp);
  }
  return line_ends;
}

function TextAttachment(props) {
  const [lines, setLines] = useState(null);
  const [stripPoint, setStripPoint] = useState([1, 0]);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState(null);

  const fromPosition = expanded ? [1, 0] : stripPoint;
  const tooLongToExpand = stripPoint[0] > MAX_DISPLAY_LINE - DISPLAY_NUM;
  const showAll = stripPoint[0] === 1;

  const { prepend, lineoffset } =
    fromPosition[0] === 1 // we use all the lines
      ? { prepend: "", lineoffset: 0 }
      : { prepend: "...\n", lineoffset: -1 };

  const handler = (text) => {
    if (_.endsWith(text, "\n")) {
      text = text.concat("<newline>");
    }

    const line_ends = getLineEnds(text);

    if (line_ends.length > DISPLAY_NUM)
      setStripPoint([
        line_ends.length - DISPLAY_NUM + 2,
        _.nth(line_ends, -DISPLAY_NUM) + 1,
      ]);

    setLines(text);
    setError(null);
  };

  const errorHandler = (error) => {
    setError(error.response.data);
    //setError(error?.response?.data?.message ? error.response.data.message : error.message);
    setLines(null);
  };

  useEffect(() => {
    if (props.file_size > MAX_DISPLAY_FILE_SIZE) {
      setError("File too big to display preview.");
    } else if (!lines) {
      loadTextFile(props.src, props.devMode, handler, errorHandler);
    }
  }, [props.src, props.file_size, props.devMode, lines]);

  const styles = StyleSheet.create({
    scrollable: {
      "overflow-y": "scroll",
      height: "55vh",
    },
    cardContent: {
      paddingTop: "0px",
      paddingBottom: "0px",
    },
  });

  const cardHeader = (
    <AttachmentAssertionCardHeader
      file_name={props.file_name}
      file_size={props.file_size}
      src={props.src}
      extra_action_items={
        lines && !tooLongToExpand && !showAll ? (
          <Button
            size="large"
            onClick={() => setExpanded(!expanded)}
            endIcon={expanded ? <ExpandLess /> : <ExpandMore />}
            style={{ width: "8em" }}
          >
            {expanded ? "Collapse" : "Expand"}
          </Button>
        ) : null
      }
    />
  );

  return (
    <Card>
      {cardHeader}
      <ErrorBoundary fallback={
        <CardBody>
          <p style={{ backgroundColor: 'red', color: 'white'}}>
            An error occured while loading content!
          </p>
        </CardBody>}>
        {lines ? (
          <CardContent className={css(styles.cardContent)}>
            <SyntaxHighlighter
              showLineNumbers
              startingLineNumber={fromPosition[0] + lineoffset}
              language="text"
              className={expanded ? css(styles.scrollable) : null}
            >
              {prepend + lines.slice(fromPosition[1])}
            </SyntaxHighlighter>
          </CardContent>
        ) : null}
        {error ? <CardContent>{error}</CardContent> : null}
      </ErrorBoundary>
    </Card>
  );
}

export default TextAttachment;
