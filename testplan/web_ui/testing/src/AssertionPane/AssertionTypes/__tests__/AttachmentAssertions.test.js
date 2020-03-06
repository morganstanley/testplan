/* Test the AttachmentAssertions components. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import {
  AttachmentAssertion,
  MatplotAssertion
} from '../AttachmentAssertions.js';

const defaultAssertionProps = {
"category": "DEFAULT",
"machine_time": "2019-02-12T17:41:43.312797+00:00",
"description": null,
"line_no": 675,
"meta_type": "entry",
"utc_time": "2019-02-12T17:41:43.312789+00:00"
}

const defaultReportUid = "123";

describe('AttachmentAssertion', () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it('renders an attached text file', () => {
    const assertionProps = {
      ...defaultAssertionProps,
      type: "Attachment",
      dst_path: 'tmpthpcdtwn-cd4f4c6e94971896a71b4a1d47785a90b19f6565-900.txt',
      filesize: 900,
      hash: 'cd4f4c6e94971896a71b4a1d47785a90b19f6565',
      orig_filename: 'tmpthpcdtwn.txt',
      source_path: '/tmp/tmpthpcdtwn.txt',
    }
    const shallowComponent = shallow(
      <AttachmentAssertion
        assertion={assertionProps}
        reportUid={defaultReportUid}
      />
    );
    expect(shallowComponent).toMatchSnapshot();
  });

  it('renders an attached image', () => {
    const assertionProps = {
      ...defaultAssertionProps,
      type: "Attachment",
      dst_path: 'tmpthpcdtwo-ad4f4c6e94971896a71b4a1d47785a90b19f6565-990.png',
      filesize: 990,
      hash: 'ad4f4c6e94971896a71b4a1d47785a90b19f6565',
      orig_filename: 'tmpthpcdtwo.png',
      source_path: '/tmp/tmpthpcdtwo.png',
    }
    const shallowComponent = shallow(
      <AttachmentAssertion
        assertion={assertionProps}
        reportUid={defaultReportUid}
      />
    );
    expect(shallowComponent).toMatchSnapshot();
  });

  it('renders an unknown filetype', () => {
    const assertionProps = {
      ...defaultAssertionProps,
      type: "Attachment",
      dst_path: 'tmpthpcdtwy-bd4f4c6e94971896a71b4a1d47785a90b19f6565-200.xyz',
      filesize: 200,
      hash: 'bd4f4c6e94971896a71b4a1d47785a90b19f6565',
      orig_filename: 'tmpthpcdtwy.xyz',
      source_path: '/tmp/tmpthpcdtwy.xyz',
    }
    const shallowComponent = shallow(
      <AttachmentAssertion
        assertion={assertionProps}
        reportUid={defaultReportUid}
      />
    );
    expect(shallowComponent).toMatchSnapshot();
  });

  it('renders an attachment using interactive API', () => {
    const assertionProps = {
      ...defaultAssertionProps,
      type: "Attachment",
      dst_path: 'tmpthpcdtwn-cd4f4c6e94971896a71b4a1d47785a90b19f6565-900.txt',
      filesize: 900,
      hash: 'cd4f4c6e94971896a71b4a1d47785a90b19f6565',
      orig_filename: 'tmpthpcdtwn.txt',
      source_path: '/tmp/tmpthpcdtwn.txt',
    }
    const shallowComponent = shallow(
      <AttachmentAssertion
        assertion={assertionProps}
        reportUid={null}
      />
    );
    expect(shallowComponent).toMatchSnapshot();
  });

});

describe('MatplotAssertion', () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it('renders an image', () => {
    const assertionProps = {
      ...defaultAssertionProps,
      type: "Matplot",
      dst_path: 'tmpthpcdtwo-ad4f4c6e94971896a71b4a1d47785a90b19f6565-860.png',
      filesize: 860,
      hash: 'ad4f4c6e94971896a71b4a1d47785a90b19f6565',
      orig_filename: 'tmpthpcdtwo.png',
      source_path: '/tmp/tmpthpcdtwo.png',
    }
    const shallowComponent = shallow(
      <AttachmentAssertion
        assertion={assertionProps}
        reportUid={defaultReportUid}
      />
    );
    expect(shallowComponent).toMatchSnapshot();
  });
});
