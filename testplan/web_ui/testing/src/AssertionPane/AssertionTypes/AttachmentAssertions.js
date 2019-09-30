/**
 * Components to render attached files in the UI.
 */
import React from 'react';
import { Row, Col } from 'reactstrap';
import { css, StyleSheet } from 'aphrodite';

import TextAttachment from './TextAttachment.js';

/**
 * Generic file attachments component.
 *
 * Provides both a direct link to download the file and optionally a rendered
 * preview of the file for supported filetypes. Currently images and text
 * files can be previewed.
 */
export const AttachmentAssertion = (props) => {
  const content = getAttachmentContent(props.assertion, props.reportUid);
  return (
    <>
      <Row>
        <Col lg='6'className={css(styles.contentSpan)}>
          <span>{content}</span>
        </Col>
      </Row>
    </>
  );
};

/* Render the attachment content, depending on the filetype. */
const getAttachmentContent = (assertion, reportUid) => {
  const file_type = assertion.orig_filename.split('.').pop();
  const file_path = assertion.dst_path;
  const get_path = `/api/v1/reports/${reportUid}/attachments/${file_path}`;

  switch (file_type) {
    case 'txt':
    case 'log':
    case 'out':
    case 'csv':
      return (
        <TextAttachment
          src={get_path}
          file_name={assertion.orig_filename}
          devMode={reportUid === "_dev"}
        />
      );

    case 'jpeg':
    case 'jpg':
    case 'bmp':
    case 'png':
        return getImageContent(get_path, assertion.description);

    default:
      // When running the development server, the real Testplan back-end is not
      // running so we can't GET the attachment. Stick in a button that
      // gives a debug message instead of the real link.
      if (reportUid === "_dev") {
        return (
          <button onClick={() => alert("Would download: " + file_path)}>
            {assertion.orig_filename}
          </button>
        );
      } else {
        return (
          <a href={get_path}>
            {assertion.orig_filename}
          </a>
        );
      }
  }
};

/*
 * Helps prepare the contents of an Image.
 *
 * @param {str} image_path
 * @param {str} description
 * @return {JSX} Content for an image to be displayed
 * @private
 */
const getImageContent = (image_path, description) => (
  <div>
    <figure className={css(styles.caption)}>
        <img src={image_path}
             className="img-responsive ..."
             alt="Cannot Find File"
        />
        <figcaption className={css(styles.caption)}>
        <a href={image_path}>
           {description ? description: "Image"}
        </a>
        </figcaption>
    </figure>
  </div>
);

export const MatplotAssertion = (props) => {
  const content = getMatplotContent(props.assertion, props.reportUid);
  return (
    <>
      <Row>
        <span>{content}</span>
      </Row>
    </>
  );
};

/*
 * Prepare the contents of a MatPlot assertion.
 *
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for MatPlot assertion
 * @private
 */
const getMatplotContent = (assertion, reportUid) => {
    const description = assertion.description;
    const get_path = (
      `/api/v1/reports/${reportUid}/attachments/${assertion.dst_path}`
    );

    if (reportUid === "_dev") {
      return (
        <figure className={css(styles.caption)}>
          Would display MatPlot from: {get_path}
          <figcaption className={css(styles.caption)}>
            <u>{description ? description: "MatPlot Image"}</u>
          </figcaption>
        </figure>
      );
    } else {
      return getImageContent(get_path, description);
    }
};

const styles = StyleSheet.create({
  caption: {
    'text-align': 'center'
  },
  contentSpan: {
    lineHeight: '110%',
  },
});

