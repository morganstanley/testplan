/**
 * EmptyReport: Render an empty report skeleton and display an error message.
 * Used as the default option when no other report URL filter is matched.
 */
import React from "react";
import { StyleSheet, css } from "aphrodite";

import Message from "../Common/Message";
import Toolbar from "../Toolbar/Toolbar";
import { COLUMN_WIDTH } from "../Common/defaults";

const EmptyReport = (props) => {
  let message;
  if (props.message) {
    message = props.message;
  } else {
    message = "404: Page Not Found";
  }

  const centerPane = <Message message={message} />;

  const noop = () => undefined;

  return (
    <div className={css(styles.emptyReport)}>
      <Toolbar
        filterBoxWidth={`${COLUMN_WIDTH}em`}
        status={undefined}
        handleNavFilter={noop}
        updateFilterFunc={noop}
        updateEmptyDisplayFunc={noop}
        updateTreeViewFunc={noop}
        updateTagsDisplayFunc={noop}
        updateTimeDisplayFunc={noop}
        extraButtons={[]}
      />
      <div
        style={{
          display: "flex",
          flex: "1",
          overflowY: "auto",
        }}
      >
        {centerPane}
      </div>
    </div>
  );
};

const styles = StyleSheet.create({ emptyReport: {} });

export default EmptyReport;
