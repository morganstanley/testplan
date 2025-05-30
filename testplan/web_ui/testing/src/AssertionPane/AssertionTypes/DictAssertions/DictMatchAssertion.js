import React from "react";
import PropTypes from "prop-types";
import MatchBaseAssertion from "./MatchBaseAssertion";

/**
 * Component that renders DictMatch assertion.
 *
 * The expected dictionary   | The actual dictionary matched
 * of the test:              | to the expected one:
 *
 * {                         | {
 *   'foo': {                |   'foo': {
 *     'alpha': 'blue',      |     'alpha': 'red',
 *     'beta': 'green',      |     'beta': 'green',
 *   }                       |   }
 *   'bar': true             |   'bar': true
 * }                         | }
 *
 *  ______________________________________
 * | Key        | Expected   | Value      |
 * |------------|------------|------------|
 * | foo        |            |            |
 * |   alpha    | blue       | red        |
 * |   beta     | green      | green      |
 * | bar        | true       | true       |
 * |____________|____________|____________|
 *
 * The grid consists of three columns: Key, Expected and Value.
 *  - Key: a key of the dictionary. Nested objects are displayed with indented
 *    keys.
 *  - Expected: expected value for the given key.
 *  - Value: Actual value for the given key.
 *
 */

export default function DictMatchAssertion(props) {
  return <MatchBaseAssertion matchType="dict" {...props} />;
}

DictMatchAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object.isRequired,
};
