import React from "react";
import { CardHeader, Button } from "@material-ui/core";
import { GetApp } from "@material-ui/icons";
import _ from "lodash";

function AttachmentAssertionCardHeader(props) {
  const idx = props.file_name.lastIndexOf(".");
  const ext_name =
    idx === -1
      ? ""
      : props.file_name
          .substring(idx + 1, props.file_name.length)
          .toLowerCase();

  return (
    <CardHeader
      title={
        ext_name === "htm" || ext_name === "html" || ext_name === "xml" ? (
          <a href={props.src} target="_blank" rel="noopener noreferrer">
            {props.file_name}
          </a>
        ) : (
          props.file_name
        )
      }
      subheader={_.round(props.file_size / 1024, 2) + "kb"}
      action={
        <>
          <Button
            size="large"
            endIcon={<GetApp />}
            href={props.src}
            download={props.file_name}
          >
            Download
          </Button>
          {props.extra_action_items}
        </>
      }
    />
  );
}

export default AttachmentAssertionCardHeader;
