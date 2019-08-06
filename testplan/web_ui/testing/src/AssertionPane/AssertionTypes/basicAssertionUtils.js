import React, {Fragment} from 'react';
import {hashCode} from '../../Common/utils';

/** @module basicAssertionUtils */

/**
 * Return a list of span components that wrap the elements of the list.
 * Each element is colored:
 *  - green if it falls in the slice and it matches the expected value,
 *  - red if it falls in the slice and it does not match the expected value or
 *  - black if it does not fall in the slice.
 *
 * @param {Array} list - List of items in the string/array.
 * @param {object} data - Object containing the status of each element.
 * @returns {Array}
 * @private
 */
function prepareSliceLists(list, data) {
  const comparisonIndices = data.reduce((accumulator, line) => {
    accumulator.push(...line[1]);
    return accumulator;
  }, []);

  const mismatchIndices = data.reduce((accumulator, line) => {
    accumulator.push(...line[2]);
    return accumulator;
  }, []);

  list = list.length > 1 ? list : list[0].split('');

  return list.map((key, index) =>
    <span key={`slice_${list.join()}_${index}`}
      style={{
        color: mismatchIndices.indexOf(index) >= 0
          ? 'red'
          : comparisonIndices.indexOf(index) >= 0
            ? 'green'
            : 'black'
      }}>
      {JSON.stringify(key)}
    </span>
  ).reduce((prev, curr) => [prev, ', ', curr]);
}

/**
 * Return a span component to display DictCheck & FixCheck assertions.
 * E.g.:
 *
 * Existence check: [26, 22, 11]
 * Absence check: [444, 555]
 *
 * Values of the list will be red if they fail to make the existence/absence
 * conditions.
 *
 * @param {object} assertion
 * @returns {object}
 * @private
 */
function prepareDictCheckContent(assertion) {
  return (
    <span>
      Existence check:
      [{assertion.has_keys.map((key, index) =>
        <span
          style={{
            color: assertion.has_keys_diff.indexOf(key) >= 0 ? 'red' : 'black'
          }}
          key={`check_${key}_${index}`}>
          {JSON.stringify(key)}
        </span>).reduce((prev, curr) => [prev, ', ', curr])}]
      <br />
      Absence check:
      [{assertion.absent_keys.map((key, index) =>
        <span
          style={{
            color: assertion.absent_keys_diff.indexOf(key) >= 0
            ? 'red'
            : 'black'
          }}
          key={`check_${key}_${index}`}>
          {JSON.stringify(key)}
        </span>).reduce((prev, curr) => [prev, ', ', curr])}]
    </span>
  );
}

/**
 * Return a span component that wraps the checked string of Regex assertions
 * where matches will be highlighted.
 *
 * @param {object} assertion
 * @returns {Array}
 * @private
 */
function prepareRegexContent(assertion) {
  const assertionString = assertion.string;
  let reconstructedString = [];
  let prevIdx = 0;

  let uid = hashCode(JSON.stringify(assertion)).toString();

  assertion.match_indexes.forEach(index => {
    reconstructedString.push(
      <span key={uid + index + '0'}>
        {assertionString.slice(prevIdx, index[0])}
      </span>
    );
    reconstructedString.push(
      <span
        style={{ backgroundColor: 'rgba(0, 123, 255, .5)' }}
        key={uid + index + '1'}
      >
        {assertionString.slice(index[0], index[1])}
      </span>
    );
    prevIdx = index[1];
  });

  reconstructedString.push(
    <span key={uid + prevIdx}>
      {assertionString.slice(prevIdx)}
    </span>
  );

  return reconstructedString;
}

/**
 *  Return a span component that wraps the checked string of RegexMatchLine
 *  assertion where matches will be highlighted.
 *
 * @param {object} assertion
 * @returns {Array}
 * @private
 */
function prepareRegexMatchLineContent(assertion) {
  let assertionString = assertion.string.split('\n');
  let reconstructedString = [];

  let uid = hashCode(JSON.stringify(assertion));

  assertion.match_indexes.forEach(index => {
    reconstructedString.push(
      <span
        key={uid + index}
        style={{ backgroundColor: 'rgba(0, 123, 255, .5)' }}
      >
        {assertionString[index[0]].slice(index[1], index[2]) + '\n'}
      </span>
    );
  });

  return reconstructedString;
}

/*
 * Prepare the contents of a report Attachment entry. Currently this just
 * provides a link to download the raw file. In future we could inspect
 * the filetype and e.g. render image files inline.
 *
 * @param {object} assertion
 * @returns {object}
 * @private
 */
function prepareAttachmentContent(assertion) {
  const paths = window.location.pathname.split('/');
  let downloadLink;

  // When running the development server, the real Testplan back-end is not
  // running so we can't GET the attachment. Stick in a button that
  // gives a debug message instead of the real link.
  if ((paths.length >= 2) && (paths[1] === '_dev')) {
    downloadLink = (
      <button onClick={() => alert("Would download: " + assertion.dst_path)}>
        {assertion.filename}
      </button>
    );
  } else if (paths.length >= 3) {
    const uid = paths[2];
    downloadLink = (
      <a href={`/api/v1/reports/${uid}/attachments/${assertion.dst_path}`}>
        {assertion.filename}
      </a>
    );
  }

  return {
    preTitle: null,
    preContent: null,
    leftTitle: null,
    rightTitle: null,
    leftContent: downloadLink,
    rightContent: null,
    postTitle: null,
    postContent: null,
  }
}

/**
 * Prepare the contents of the BasicAssertion component.
 *
 * @param {object} assertion
 * @returns {{
 *    preTitle: object|string|null,
 *    preContent: object|string|null,
 *    leftTitle: object|string|null,
 *    rightTitle: object|string|null,
 *    leftContent: object|string|null,
 *    rightContent: object|string|null,
 *    postTitle: object|string|null,
 *    postContent: object|string|null
 * }}
 * @public
 */
function prepareBasicContent(assertion) {
  // This is a long function with lots of if elses, however I think it shows
  // what it is doing a clearly and simply as it can
  let content = {
    preTitle: null,
    preContent: null,
    leftTitle: 'Expected:',
    rightTitle: 'Value:',
    leftContent: assertion.second,
    rightContent: assertion.first,
    postTitle: null,
    postContent: null,
  };

  var uid = hashCode(JSON.stringify(assertion));

  if (assertion.type === 'Log') {
    content['preContent'] = (
      <span>
        {assertion.message !== undefined ? assertion.message : null}
      </span>
    );
    content['leftTitle'] = null;
    content['rightTitle'] = null;

  } else if (assertion.type === 'Equal') {
    content['leftContent'] = <span>{assertion.second}</span>;

  } else if (assertion.type === 'NotEqual') {
    content['leftContent'] = <span>&lt;not&gt; {assertion.second}</span>;

  } else if (['Greater', 'GreaterEqual', 'Less', 'LessEqual']
    .indexOf(assertion.type) >= 0) {
    content['leftContent'] =
      <span>value {assertion.label} {assertion.second}</span>;

  } else if (assertion.type === 'IsClose') {
    content['leftContent'] =
      <span>
        value {assertion.label} {assertion.second}
        &nbsp;within rel_tol={assertion.rel_tol} or abs_tol={assertion.abs_tol}
      </span>;

  } else if (assertion.type === 'IsTrue') {
    content['leftContent'] = <span>value is True</span>;
    content['rightContent'] =
      <span>{assertion.passed ? `True` : `False`}</span>;

  } else if (assertion.type === 'IsFalse') {
    content['leftContent'] = <span>value is False</span>;
    content['rightContent'] =
      <span>{assertion.passed ? `False` : `True`}</span>;

  } else if (assertion.type === 'Fail') {
    content['leftContent'] = null;
    content['rightContent'] = null;
    content['leftTitle'] = null;
    content['rightTitle'] = null;

  } else if (assertion.type === 'Contain') {
    content['leftContent'] = <span>{assertion.member} &lt;in&gt; value</span>;
    content['rightContent'] = <span>{assertion.container}</span>;

  } else if (assertion.type === 'NotContain') {
    content['leftContent'] =
      <span>{assertion.member} &lt;not in&gt; value</span>;
    content['rightContent'] = <span>{assertion.container}</span>;

  } else if (assertion.type === 'LineDiff') {
    content['leftContent'] =
      <span>
        {assertion.delta.map(
          (line, index) => {
            return (
              <span
                key={"LineDiffleftContent"+uid+index}
                style={{ whiteSpace: 'pre' }}
              >
                {line}
              </span>
            );
          }
        )}
      </span>;
    content['rightContent'] = null;
    content['leftTitle'] =
      <span>{!assertion.passed ? 'Differences:' : 'No differences.'}</span>;
    content['rightTitle'] = null;

  } else if (['ExceptionRaised', 'ExceptionNotRaised']
    .indexOf(assertion.type) >= 0
  ) {
    content['leftContent'] = <span>{assertion.expected_exceptions}</span>;
    content['rightContent'] =
      <span>
        {assertion.raised_exception[0]} (value: {assertion.raised_exception[1]})
      </span>;
    content['leftTitle'] = <span>Expected exceptions:</span>;
    content['rightTitle'] = <span>Raised exceptions:</span>;

  } else if (
    [
      'RegexMatch',
      'RegexMatchNotExists',
      'RegexSearch',
      'RegexSearchNotExists',
      'RegexFindIter'
    ].indexOf(assertion.type) >= 0
  ) {
    content['leftContent'] = <span>{assertion.pattern}</span>;
    content['rightContent'] =
      <span style={{ whiteSpace: 'pre' }}>
        {prepareRegexContent(assertion)}
      </span>;
    content['leftTitle'] = <span>Pattern:</span>;
    content['rightTitle'] = <span>String:</span>;

  } else if (assertion.type === 'RegexMatchLine') {
    content['leftContent'] = <span>{assertion.pattern}</span>;
    content['rightContent'] =
      <span style={{ whiteSpace: 'pre' }}>
        {prepareRegexMatchLineContent(assertion)}
      </span>;
    content['leftTitle'] = <span>Pattern:</span>;
    content['rightTitle'] = <span>String:</span>;

  } else if (assertion.type === 'XMLCheck') {
    content['leftContent'] = <span>{assertion.xpath}</span>;
    content['rightContent'] =
      <span style={{ whiteSpace: 'pre' }}>
        {assertion.xml.replace(/ {12}/g, '')}
      </span>;
    content['leftTitle'] = <span>Expected XPath:</span>;
    content['rightTitle'] = <span>XML:</span>;

  } else if (
    ['EqualSlices', 'EqualExcludeSlices'].indexOf(assertion.type) >= 0
  ) {
    content['preTitle'] = <span>Slices:</span>;
    content['preContent'] =
      <Fragment>
        <span style={{ whiteSpace: 'pre' }}>
          {assertion.data.map(slice => slice[0]).join('\n')}
        </span>
        <hr />
      </Fragment>;
    content['leftContent'] =
      <span>[{prepareSliceLists(assertion.expected, assertion.data)}]</span>;
    content['rightContent'] =
      <span>[{prepareSliceLists(assertion.actual, assertion.data)}]</span>;
    content['leftTitle'] = <span>Expected:</span>;
    content['rightTitle'] = <span>Value:</span>;

  } else if (['DictCheck', 'FixCheck'].indexOf(assertion.type) >= 0) {
    content['leftTitle'] = null;
    content['rightTitle'] = null;
    content['preContent'] = prepareDictCheckContent(assertion);
  } else if (assertion.type === 'Attachment') {
    content = prepareAttachmentContent(assertion);
  }

  return content;
}


export {
  prepareBasicContent,
};
