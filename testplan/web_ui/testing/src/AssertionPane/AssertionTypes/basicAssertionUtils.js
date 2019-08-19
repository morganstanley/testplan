import React, {Fragment} from 'react';
import {hashCode} from '../../Common/utils';

/** @module basicAssertionUtils */

/**
 * Content required to render a basic assertion. The content is rendered by the
 * BasicAssertion component, refer to that component for a diagram of how each
 * content section is displayed.
 *
 * @typedef {Object} AssertionContent
 * @property {object|string|null} preTitle - Content above the assertion title
 * @property {object|string|null} preContent - Content between the preTitle and
 *                                             the title
 * @property {object|string|null} leftTitle - Left side of the title
 * @property {object|string|null} rightTitle - Right side of the title
 * @property {object|string|null} leftContent - Left side of the main content
 * @property {object|string|null} rightContent - Right side of the main content
 * @property {object|string|null} postTitle - Content immediately below the
 *                                            title
 * @property {object|string|null} postContent - Final content of assertion
 */

/**
 * Prepare the content for the Log assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for Log assertion
 * @private
 */
function prepareLogContent(assertion, defaultContent) {
  const preContent = (
    <span>
      {assertion.message !== undefined ? assertion.message : null}
     </span>
  );

  return {
    ...defaultContent,
    preContent: preContent,
    leftTitle: null,
    rightTitle: null,
  };
}

/**
 * Prepare the content for the Equal assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for Equal assertion
 * @private
 */
function prepareEqualContent(assertion, defaultContent) {
  const leftContent = <span>{assertion.second}</span>;

  return {
    ...defaultContent,
    leftContent: leftContent,
  };
}

/**
 * Prepare the content for the NotEqual assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for NotEqual assertion
 * @private
 */
function prepareNotEqualContent(assertion, defaultContent) {
  const leftContent = <span>&lt;not&gt; {assertion.second}</span>;

  return {
    ...defaultContent,
    leftContent: leftContent,
  };
}

/**
 * Prepare the content for comparison assertions (lessThan,
 * greaterThan etc.).
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for comparison assertion
 * @private
 */
function prepareComparisonContent(assertion, defaultContent) {
    const leftContent = (
      <span>value {assertion.label} {assertion.second}</span>
    );

  return {
    ...defaultContent,
    leftContent: leftContent,
  };
}

/**
 * Prepare the content for the IsClose assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for IsClose assertion
 * @private
 */
function prepareIsCloseContent(assertion, defaultContent) {
  const leftContent = (
    <span>
      value {assertion.label} {assertion.second}
      &nbsp;within rel_tol={assertion.rel_tol} or abs_tol={assertion.abs_tol}
    </span>
  );

  return {
    ...defaultContent,
    leftContent: leftContent,
  };
}

/**
 * Prepare the content for the IsTrue assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for IsTrue assertion
 * @private
 */
function prepareIsTrueContent(assertion, defaultContent) {
  const leftContent = <span>value is True</span>;
  const rightContent = (
    <span>{assertion.passed ? `True` : `False`}</span>
  );

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
  };
}

/**
 * Prepare the content for the IsFalse assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for IsFalse assertion
 * @private
 */
function prepareIsFalseContent(assertion, defaultContent) {
  const leftContent = <span>value is False</span>;
  const rightContent = (
    <span>{assertion.passed ? `False` : `True`}</span>
  );

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
  };
}

/**
 * Prepare the content for the Fail assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for Fail assertion
 * @private
 */
function prepareFailContent(assertion, defaultContent) {
  return {
    ...defaultContent,
    leftTitle: null,
    rightTitle: null,
    leftContent: null,
    rightContent: null,
  };
}

/**
 * Prepare the content for the Contain assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for Contain assertion
 * @private
 */
function prepareContainContent(assertion, defaultContent) {
  const leftContent = <span>{assertion.member} &lt;in&gt; value</span>;
  const rightContent = <span>{assertion.container}</span>;
  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
  };
}

/**
 * Prepare the content for the NotContain assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for NotContain assertion
 * @private
 */
function prepareNotContainContent(assertion, defaultContent) {
  const leftContent = (
    <span>{assertion.member} &lt;not in&gt; value</span>
  );
  const rightContent = <span>{assertion.container}</span>;

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
  };
}

/**
 * Prepare the content for the LineDiff assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for LineDiff assertion
 * @private
 */
function prepareLineDiffContent(assertion, defaultContent) {
  const uid = hashCode(JSON.stringify(assertion));
  const leftContent = (
    <span>
      {
        assertion.delta.map(
          (line, index) => {
            return (
              <span
                key={"LineDiffleftContent" + uid + index}
                style={{ whiteSpace: 'pre' }}
              >
                {line}
              </span>
            );
          }
        )
      }
    </span>
  );
  const leftTitle = (
    <span>{!assertion.passed ? 'Differences:' : 'No differences.'}</span>
  );

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: null,
    leftTitle: leftTitle,
    rightTitle: null,
  };
}

/*
 * Prepare the content for the ExceptionRaised and ExceptionNotRaised
 * assertions.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for exception assertion
 * @private
 */
function prepareExceptionContent(assertion, defaultContent) {
  const leftContent = <span>{assertion.expected_exceptions}</span>;
  const rightContent = (
    <span>
      {assertion.raised_exception[0]} (value: {assertion.raised_exception[1]})
    </span>
  );
  const leftTitle = <span>Expected exceptions:</span>;
  const rightTitle = <span>Raised exceptions:</span>;

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
    leftTitle: leftTitle,
    rightTitle: rightTitle,
  };
}

/*
 * Prepare the content for the RegexMatch, RegexMatchNotExists, RegexSearch,
 * RegexSearchNotExists and RegexFindIter assertions.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for regex assertion
 * @private
 */
function prepareRegexContent(assertion, defaultContent) {
  const assertionString = assertion.string;
  let reconstructedString = [];
  let prevIdx = 0;
  const uid = hashCode(JSON.stringify(assertion)).toString();

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

  const leftContent = (
    <div>
      <span>{assertion.pattern}</span>
      <span>
        {
          assertion.condition && (
            <div key={assertion.uid}>
              <br/>
              <strong>Condition:</strong>
              <br/>
              <span>{assertion.condition}</span>
            </div>
          )
        }
      </span>
    </div>
  );
  const rightContent = (
    <span style={{ whiteSpace: 'pre' }}>
      {reconstructedString}
    </span>
  );
  const leftTitle = <span>Pattern:</span>;
  const rightTitle = <span>String:</span>;

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
    leftTitle: leftTitle,
    rightTitle: rightTitle,
  };
}

/**
 * Prepare the content for the RegexMatchLine assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for RegexMatchLine assertion
 * @private
 */
function prepareRegexMatchLineContent(assertion, defaultContent) {
  const assertionString = assertion.string.split('\n');
  const uid = hashCode(JSON.stringify(assertion));
  const reconstructedString = assertion.match_indexes.map((index) => (
      <span
        key={uid + index}
        style={{ backgroundColor: 'rgba(0, 123, 255, .5)' }}
      >
        {assertionString[index[0]].slice(index[1], index[2]) + '\n'}
      </span>
  ));

  const leftContent = <span>{assertion.pattern}</span>;
  const rightContent = (
    <span style={{ whiteSpace: 'pre' }}>
      {reconstructedString}
    </span>
  );
  const leftTitle = <span>Pattern:</span>;
  const rightTitle = <span>String:</span>;

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
    leftTitle: leftTitle,
    rightTitle: rightTitle,
  };
}

/**
 * Prepare the content for the XMLCheck assertion.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for XMLCheck assertion
 * @private
 */
function prepareXMLCheckContent(assertion, defaultContent) {
  const leftContent = <span>{assertion.xpath}</span>;
  const rightContent = (
    <span style={{ whiteSpace: 'pre' }}>
      {assertion.xml.replace(/ {12}/g, '')}
    </span>
  );
  const leftTitle = <span>Expected XPath:</span>;
  const rightTitle = <span>XML:</span>;

  return {
    ...defaultContent,
    leftContent: leftContent,
    rightContent: rightContent,
    leftTitle: leftTitle,
    rightTitle: rightTitle,
  };
}

/**
 * Prepare the content for the EqualSlices and EqualExcludesSlices
 * assertions.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for equal slices assertion
 * @private
 */
function prepareEqualSlicesContent(assertion, defaultContent) {
  const preTitle = <span>Slices:</span>;
  const preContent = (
    <Fragment>
      <span style={{ whiteSpace: 'pre' }}>
        {assertion.data.map(slice => slice[0]).join('\n')}
      </span>
      <hr />
    </Fragment>
  );
  const leftContent = (
    <span>[{prepareSliceLists(assertion.expected, assertion.data)}]</span>
  );
  const rightContent = (
    <span>[{prepareSliceLists(assertion.actual, assertion.data)}]</span>
  );
  const leftTitle = <span>Expected:</span>;
  const rightTitle = <span>Value:</span>;

  return {
    ...defaultContent,
    preTitle: preTitle,
    preContent: preContent,
    leftContent: leftContent,
    rightContent: rightContent,
    leftTitle: leftTitle,
    rightTitle: rightTitle,
  };
}

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
 * Prepare the content for the DictCheck and FixCheck assertions.
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for dict match assertion
 * @private
 */
function prepareDictCheckContent(assertion, defaultContent) {
  const preContent = (
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

  return {
    ...defaultContent,
    preContent: preContent,
    leftTitle: null,
    rightTitle: null,
  };
}

/*
 * Prepare the contents of a report Attachment entry. Currently this just
 * provides a link to download the raw file. In future we could inspect
 * the filetype and e.g. render image files inline.
 *
 * @param {object} assertion
 * @param {AssertionContent} defaultContent
 * @return {AssertionContent} Content for attachment assertion
 * @private
 */
function prepareAttachmentContent(assertion, defaultContent) {
  const paths = window.location.pathname.split('/');
  let downloadLink;

  // When running the development server, the real Testplan back-end is not
  // running so we can't GET the attachment. Stick in a button that
  // gives a debug message instead of the real link.
  if ((paths.length >= 2) && (paths[1] === '_dev')) {
    downloadLink = (
      <button onClick={() => alert("Would download: " + assertion.dst_path)}>
        {assertion.orig_filename}
      </button>
    );
  } else if (paths.length >= 3) {
    const uid = paths[2];
    downloadLink = (
      <a href={`/api/v1/reports/${uid}/attachments/${assertion.dst_path}`}>
        {assertion.orig_filename}
      </a>
    );
  }

  return {
    ...defaultContent,
    leftTitle: null,
    rightTitle: null,
    leftContent: downloadLink,
    rightContent: null,
  };
}

/**
 * Prepare the contents of the BasicAssertion component.
 *
 * @param {object} assertion
 * @returns {AssertionContent} Content for the assertion based on its type.
 * @public
 */
function prepareBasicContent(assertion) {
  // Default content for a basic assertion. Specific assertion types will
  // modify this content.
  const defaultContent = {
    preTitle: null,
    preContent: null,
    leftTitle: 'Expected:',
    rightTitle: 'Value:',
    leftContent: assertion.second,
    rightContent: assertion.first,
    postTitle: null,
    postContent: null,
  }

  // Fan out to the relevant function to prepare content for each assertion
  // type.
  switch (assertion.type) {
    case 'Log':
      return prepareLogContent(assertion, defaultContent);

    case 'Equal':
      return prepareEqualContent(assertion, defaultContent);

    case 'NotEqual':
      return prepareNotEqualContent(assertion, defaultContent);

    case 'Greater':
    case 'GreaterEqual':
    case 'Less':
    case 'LessEqual':
      return prepareComparisonContent(assertion, defaultContent);

    case 'IsClose':
      return prepareIsCloseContent(assertion, defaultContent);

    case 'IsTrue':
      return prepareIsTrueContent(assertion, defaultContent);

    case 'IsFalse':
      return prepareIsFalseContent(assertion, defaultContent);

    case 'Fail':
      return prepareFailContent(assertion, defaultContent);

    case 'Contain':
      return prepareContainContent(assertion, defaultContent);

    case 'NotContain':
      return prepareNotContainContent(assertion, defaultContent);

    case 'LineDiff':
      return prepareLineDiffContent(assertion, defaultContent);

    case 'ExceptionRaised':
    case 'ExceptionNotRaised':
      return prepareExceptionContent(assertion, defaultContent);


    case 'RegexMatch':
    case 'RegexMatchNotExists':
    case 'RegexSearch':
    case 'RegexSearchNotExists':
    case 'RegexFindIter':
      return prepareRegexContent(assertion, defaultContent);

    case 'RegexMatchLine':
      return prepareRegexMatchLineContent(assertion, defaultContent);


    case 'XMLCheck':
      return prepareXMLCheckContent(assertion, defaultContent);

    case 'EqualSlices':
    case 'EqualExcludeSlices':
      return prepareEqualSlicesContent(assertion, defaultContent);


    case 'DictCheck':
    case 'FixCheck':
      return prepareDictCheckContent(assertion, defaultContent);

    case 'Attachment':
      return prepareAttachmentContent(assertion, defaultContent);

    default:
      return defaultContent;
  }
}

export {
  prepareBasicContent,
};

