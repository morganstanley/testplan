import React from 'react';
import PropTypes from 'prop-types';
import base64url from 'base64url';
import NavBreadcrumbs from "./NavBreadcrumbs";
import NavList from "./NavList";
import TreeViewNav from "./TreeView";
import InteractiveTreeViewNav from './InteractiveTreeView';
import {
    GetSelectedUid,
    GetNavEntries,
    GetInteractiveNavEntries,
    GetNavBreadcrumbs
} from "./navUtils";

/**
 * Nav component:
 *   * render breadcrumbs menu.
 *   * render list menu.
 *   * handle clicking through menus, tracking what has been selected.
 *   * auto select entries if the list is empty or has 1 entry.
 *   * Adds extra buttons for running testcases interactively and controlling
 *     environments.
 */
const Nav = (props) => {
    const breadCrumbEntries = props.interactive ? (
        GetNavBreadcrumbs(props.selected)
    ) : props.selected;
    const encoder = props.interactive ? base64url : null;
    return (
        <>
        <NavBreadcrumbs
            entries={breadCrumbEntries}
            url={props.url}
            uidEncoder = {encoder}
        />
        {renderNavigation(props)}
        </>
    );
};

Nav.propTypes = {
    /** Interactive mode flag */
    interactive: PropTypes.bool,
    /** Testplan report */
    report: PropTypes.object,
    /** Selected navigation entries. */
    selected: PropTypes.arrayOf(PropTypes.object),
    /** Function to handle saving the assertions found by the Nav */
    saveAssertions: PropTypes.func,
    /** Entity filter */
    filter: PropTypes.string,
    /** Flag to display tree view or default view */
    treeView: PropTypes.bool,
    /** Flag to display tags on navbar */
    displayTags: PropTypes.bool,
    /** Flag to display execution time on navbar */
    displayTime: PropTypes.bool,
    /** Flag to display empty testcase on navbar */
    displayEmpty: PropTypes.bool,

    url: PropTypes.string
};

const renderNavigation = (props) => {
    if (props.treeView && !props.interactive) {
        const breadCrumbEntries = props.selected;
        const navEntries = props.report ? props.report.entries : [];
        return <TreeViewNav
            width={props.navListWidth}
            entries={navEntries}
            breadcrumbLength={breadCrumbEntries.length}
            handleColumnResizing={props.handleColumnResizing}
            filter={props.filter}
            displayEmpty={props.displayEmpty}
            displayTags={props.displayTags}
            displayTime={props.displayTime}
            selected={props.selected}
            selectedUid={GetSelectedUid(props.selected)}
            url={props.url}
        />;
    }
    else if (!props.treeView && !props.interactive) {
        const breadCrumbEntries = props.selected;
        const navEntries = GetNavEntries(props.selected);
        return <NavList
            interactive={false}
            width={props.navListWidth}
            entries={navEntries}
            breadcrumbLength={breadCrumbEntries.length}
            handleColumnResizing={props.handleColumnResizing}
            filter={props.filter}
            displayEmpty={props.displayEmpty}
            displayTags={props.displayTags}
            displayTime={props.displayTime}
            selectedUid={GetSelectedUid(props.selected)}
            handleClick={props.handleClick}
            envCtrlCallback={props.envCtrlCallback}
            url={props.url}
        />;
    }
    else if (props.treeView && props.interactive) {
        const breadCrumbEntries = GetNavBreadcrumbs(props.selected);
        const navEntries = props.report ? props.report.entries : [];
        return <InteractiveTreeViewNav
            width={props.navListWidth}
            entries={navEntries}
            breadcrumbLength={breadCrumbEntries.length}
            handleColumnResizing={props.handleColumnResizing}
            filter={null}
            displayEmpty={true}
            displayTags={false}
            displayTime={false}
            selected={props.selected}
            selectedUid={GetSelectedUid(props.selected)}
            handleClick={props.handleClick}
            envCtrlCallback={props.envCtrlCallback}
            url={props.url}
        />;
    }
    else if (!props.treeView && props.interactive) {
        const breadCrumbEntries = GetNavBreadcrumbs(props.selected);
        const navEntries = GetInteractiveNavEntries(props.selected);
        return <NavList
            interactive={true}
            width={props.navListWidth}
            entries={navEntries}
            breadcrumbLength={breadCrumbEntries.length}
            handleColumnResizing={props.handleColumnResizing}
            filter={null}
            displayEmpty={true}
            displayTags={false}
            displayTime={false}
            selectedUid={GetSelectedUid(props.selected)}
            handleClick={props.handleClick}
            envCtrlCallback={props.envCtrlCallback}
            url={props.url}
        />;
    }
};

export default Nav;