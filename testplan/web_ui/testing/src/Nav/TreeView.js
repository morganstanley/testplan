import React from 'react';
import PropTypes from 'prop-types';
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';
import Column from './Column';
import NavEntry from './NavEntry';
import { applyAllFilters } from './navUtils';
import { STATUS } from "../Common/defaults";
import { CATEGORIES } from "../Common/defaults";
import { generatePath } from 'react-router';
import { NavLink } from 'react-router-dom';
import TagList from './TagList';


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

const LeafNodeStyle = {
  webkitUserSelect: "text",
  MozUserSelect: "text",
  MsUserSelect: "text",
  UserSelect: "text",
  textDecoration: 'none'
};

const createTree = (props) => {
  let entries = applyAllFilters(props, props.entries);
  return Array.isArray(entries) ?
    entries.map((entry) => createTreeHelper(props, entry)) : null;
};

const createTreeHelper = (props, entry) => {
  return entry.category === CATEGORIES['testcase'] ?
    createLeafNode(props, entry) : createNode(props, entry);
};

const createLeafNode = (props, entry) => {
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
  return (
    <TreeItem
      nodeId={entry.uid || entry.hash}
      key={entry.uid || entry.hash}
      label={
        <NavLink
          style={LeafNodeStyle}
          key={entry.hash || entry.uid}
          to={linkTo}>
          {tags}
          {createNavEntry(props, entry)}
        </NavLink>
      }></TreeItem>
  );
};

const createNode = (props, entry) => {
  return (
    <TreeItem
      nodeId={entry.uid || entry.hash}
      key={entry.uid || entry.hash}
      label={createNavEntry(props, entry)}>
      {Array.isArray(entry.entries) ?
        entry.entries.map((entry) => createTreeHelper(props, entry)) : null}
    </TreeItem>
  );
};

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