import React from "react";
import { CardHeader, Button } from "@material-ui/core";
import { GetApp } from "@material-ui/icons";
import _ from "lodash";

function AttachmentAssertionCardHeader(props) {
  return (
    <CardHeader
      title={props.file_name}
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
