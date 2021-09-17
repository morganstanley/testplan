import React from 'react';
import PropTypes from 'prop-types';
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';
import { css, StyleSheet } from 'aphrodite';
import Column from './Column';
import NavEntry from './NavEntry';
import { applyAllFilters } from './navUtils';
import { STATUS, MEDIUM_GREY } from "../Common/defaults";
import { CATEGORIES } from "../Common/defaults";
import { generatePath } from 'react-router';
import { NavLink } from 'react-router-dom';
import TagList from './TagList';
import { makeStyles } from '@material-ui/core/styles';

/**
 * Render a vertical list of all the currently selected entries children.
 */
const TreeViewNav = (props) => {
  return (
    <>
      <Column
        width={props.width}
        handleColumnResizing={props.handleColumnResizing}>
        <TreeView
          className={css(styles.treeView)}
          disableSelection={true}
          defaultCollapseIcon={<ExpandMoreIcon />}
          defaultExpandIcon={<ChevronRightIcon />}>
          {createTree(props)}
        </TreeView>
      </Column >
    </>

  );
};

TreeViewNav.propTypes = {
  /** Nav list entries to be displayed */
  entries: PropTypes.arrayOf(PropTypes.shape({
    uid: PropTypes.string,
    name: PropTypes.string,
    description: PropTypes.string,
    status: PropTypes.oneOf(STATUS),
    counter: PropTypes.shape({
      passed: PropTypes.number,
      failed: PropTypes.number,
    }),
  })),
  /** Number of entries in the breadcrumb menu */
  breadcrumbLength: PropTypes.number,
  /** Function to handle Nav list resizing */
  handleColumnResizing: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display tags on navbar */
  displayTags: PropTypes.bool,
  /** Flag to display execution time on navbar */
  displayTime: PropTypes.bool,
  /** Entry uid to be focused */
  selectedUid: PropTypes.string,

  url: PropTypes.string
};

export default TreeViewNav;

const createTree = (props) => {
  let entries = applyAllFilters(props, props.entries);
  return Array.isArray(entries) ?
    entries.map((entry) => createNode(props, entry)) : null;
};

const createNode = (props, entry) => {
  let [reportuid, ...selectionuids] = entry.uids;
  const linkTo = generatePath(props.url,
    {
      uid: reportuid,
      selection: selectionuids
    });
  const tags = (
    (props.displayTags && entry.tags)
      ? <TagList entryName={entry.name} tags={entry.tags} />
      : null
  );
  const treeViewClasses = createTreeViewStyles();
  return (
    <TreeItem
      classes={{
        label: treeViewClasses.treeItemLabel,
        iconContainer: treeViewClasses.iconContainer
      }}
      nodeId={entry.uid || entry.hash}
      key={entry.uid || entry.hash}
      onLabelClick={event => {
        event.preventDefault();
      }}
      label={
        <NavLink
          className={css(styles.leafNode)}
          key={entry.hash || entry.uid}
          to={linkTo}>
          {tags}
          {createNavEntry(props, entry)}
        </NavLink>
      }>
      {entry.category === CATEGORIES['testcase'] ?
        null : continueTreeBranch(props, entry)}
    </TreeItem>
  );
};

const continueTreeBranch = (props, entry) => {
  return Array.isArray(entry.entries) ?
    entry.entries.map((entry) => createNode(props, entry)) : null
}

const createNavEntry = (props, entry) => {
  return (
    <NavEntry
      name={entry.name}
      description={entry.description}
      status={entry.status}
      type={entry.category}
      caseCountPassed={entry.counter.passed}
      caseCountFailed={entry.counter.failed + (entry.counter.error || 0)}
      executionTime={(entry.timer && entry.timer.run) ? (
        (new Date(entry.timer.run.end)).getTime() -
        (new Date(entry.timer.run.start)).getTime()) / 1000 : null}
      displayTime={props.displayTime} />
  );
};

const createTreeViewStyles = makeStyles({
  treeItemLabel: {
    padding: '5px 0px',
    overflow: 'hidden',
    '&:hover': {
      backgroundColor: MEDIUM_GREY
    },
  },

  iconContainer: {
    cursor: 'pointer'
  }
});

const styles = StyleSheet.create({
  treeView: {
    'overflow-y': 'auto',
    'overflow-x': 'hidden',
    'height': '100%',
  },

  leafNode: {
    textDecoration: 'none',
    color: '#495057'
  }
});