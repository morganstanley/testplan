import React from "react";
import PropTypes from "prop-types";
import MatchAllBaseAssertion from "./MatchAllBaseAssertion";

/**
 * Component that renders DictMatchAll assertion.
 *
 * The expected list of      | The actual list of dictionaries matched
 * dictionaries of the test: | to the expected ones:
 *
 * [                         | [
 *   {'foo': 12, 'bar': 22}, |   {'foo': 13, 'bar': 25},
 *   {'foo': 13, 'bar': 23}  |   {'foo': 12, 'bar': 22}
 * ]                         | ]
 *
 *
 * 1/2: expected[1] vs values[0]
 *  ______________________________________
 * | Key        | Expected   | Value      |
 * |------------|------------|------------|
 * | foo        | 13         | 13         |
 * | bar        | 23         | 25         |
 * |____________|____________|____________|
 *
 * 2/2: expected[0] vs values[1]
 *  ______________________________________
 * | Key        | Expected   | Value      |
 * |------------|------------|------------|
 * | foo        | 12         | 12         |
 * | bar        | 22         | 22         |
 * |____________|____________|____________|
 *
 * For each comparison pair, the grid consists of three columns:
 * Key, Expected and Value.
 *  - Key: a key of the dictionary. Nested objects are displayed with indented
 *    keys.
 *  - Expected: expected value for the given key.
 *  - Value: Actual value for the given key.
 *
 */
export default function DictMatchAllAssertion(props) {
    return <MatchAllBaseAssertion matchType="dict" {...props} />;
}

DictMatchAllAssertion.propTypes = {
    /** Assertion being rendered */
    assertion: PropTypes.object.isRequired,
};
