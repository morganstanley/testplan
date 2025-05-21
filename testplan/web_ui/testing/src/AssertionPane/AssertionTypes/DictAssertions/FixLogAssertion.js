import React from "react";
import PropTypes from "prop-types";
import LogBaseAssertion from "./LogBaseAssertion";

/**
 * Component that renders FixLog assertion.
 *
 * The actual dictionary of the test:
 *
 * {
 *   'foo': {
 *     'alpha': 'blue',
 *     'beta': 'green',
 *   }
 *   'bar': true
 * }
 *
 *  _________________________
 * | Key        | Value      |
 * |------------|------------|
 * | *foo       |            |
 * |   *alpha   | blue       |
 * |   *beta    | green      |
 * | *bar       | true       |
 * |____________|____________|
 *
 * The grid consists of two columns: Key and Value.
 *  - Key: a key of the dictionary. Nested objects are displayed with indented
 *    keys.
 *  - Value: Actual value for the given key.
 *
 */
export default function FixLogAssertion(props) {
  return <LogBaseAssertion logType="fix" {...props} />;
}

FixLogAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object.isRequired,
};
