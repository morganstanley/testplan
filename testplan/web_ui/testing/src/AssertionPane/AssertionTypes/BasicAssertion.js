import React, { Fragment } from "react";
import PropTypes from "prop-types";
import { css, StyleSheet } from "aphrodite";
import { Col, Row } from "reactstrap";

import { prepareBasicContent } from "./basicAssertionUtils";

/**
 * Component used to render basic, text based assertions (e.g.: basic
 * comparisons, regex matches, etc). It is designed to render the following
 * grid:
 *  _______________________________
 * | preTitle                      |
 * |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
 * | preContent                    |
 * |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
 * | leftTitle     | rightTitle    |
 * |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
 * | leftContent   | rightContent  |
 * |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
 * | postTitle                     |
 * |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
 * | postContent                   |
 * |_______________________________|
 *
 * basicAssertionUtils' {@link prepareBasicContent} function is called to fetch
 * the data to be displayed. It returns an object that fills the aforementioned
 * grid with data.
 */
function BasicAssertion({ assertion }) {
  const {
    preTitle,
    preContent,
    leftTitle,
    rightTitle,
    leftContent,
    rightContent,
    postTitle,
    postContent,
  } = prepareBasicContent(assertion);

  return (
    <Fragment>
      <Row>
        <Col lg="12">
          <strong>{preTitle}</strong>
        </Col>
      </Row>
      <Row>
        <Col lg="12" className={css(styles.contentSpan)}>
          {preContent}
        </Col>
      </Row>
      <Row>
        <Col lg="6">
          <strong>{leftTitle}</strong>
        </Col>
        <Col lg="6">
          <strong>{rightTitle}</strong>
        </Col>
      </Row>
      <Row>
        <Col lg="6" className={css(styles.contentSpan)}>
          <span>{leftContent}</span>
        </Col>
        <Col lg="6" className={css(styles.contentSpan)}>
          <span>{rightContent}</span>
        </Col>
      </Row>
      <Row>
        <Col lg="12">
          <strong>{postTitle}</strong>
        </Col>
      </Row>
      <Row>
        <Col lg="12" className={css(styles.contentSpan)}>
          {postContent}
        </Col>
      </Row>
    </Fragment>
  );
}

BasicAssertion.propTypes = {
  /**  Assertion being rendered */
  assertion: PropTypes.object,
};

const styles = StyleSheet.create({
  contentSpan: {
    lineHeight: "110%",
    "overflow-x": "auto",
  },
});

export default BasicAssertion;
