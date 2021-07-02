/**
 * EmptyReport: Render an empty report skeleton and display an error message.
 * Used as the default option when no other report URL filter is matched.
 */
import React from 'react';
import {StyleSheet, css} from 'aphrodite';

import Message from '../Common/Message';
import Toolbar from '../Toolbar/Toolbar';
import {TimeButton} from '../Toolbar/Buttons';
import Nav from '../Nav/Nav';
import {COLUMN_WIDTH} from "../Common/defaults";

const EmptyReport = (props) => {
  let message;
  if (props.message) {
    message = props.message;
  } else {
    message = "404: Page Not Found";
  }

  const centerPane = (
    <Message
      message={message}
      left={`${COLUMN_WIDTH}em`}
    />
  );

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
        extraButtons={[<TimeButton
            key="time-button"
            status={undefined}
            updateTimeDisplayCbk={noop}
          />]}
      />
      <Nav
        report={null}
        saveAssertions={noop}
        filter={undefined}
        treeView={false}
        displayEmpty={true}
        displayTags={false}
        displayTime={false}
      />
      {centerPane}
    </div>
  );
};

const styles = StyleSheet.create({ emptyReport: {} });

export default EmptyReport;

