/* Test the AttachmentAssertions components. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import Typography from '@material-ui/core/Typography';

import { AttachedDirAssertion } from '../AttachedDirAssertion';

const defaultAssertionProps = {
  "category": "DEFAULT",
  "machine_time": "2019-03-26T17:20:45.793127+00:00",
  "description": null,
  "line_no": 676,
  "meta_type": "entry",
  "utc_time": "2019-03-26T17:20:45.793132+00:00"
}

const defaultReportUid = "123";

describe('AttachedDirAssertion', () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it('renders an attached directory', () => {
    const assertionProps = {
      ...defaultAssertionProps,
      type: "Directory",
      dst_path: '4ac48da114046bd1246631bc1feb04c4',
      source_path: '/tmp/testplan/basic-test/mtest/scratch/4ac48da114046bd1246631bc1feb04c4',
      ignore: null,
      only: ['*.py', '*.html'],
      recursive: true,
      file_list: [
        'index.html',
        '__init__.py',
        'subdir/module.py',
      ],
    }
    const shallowComponent = shallow(
      <AttachedDirAssertion
        assertion={assertionProps}
        reportUid={defaultReportUid}
      />
    );

    expect(shallowComponent.find(Typography).first().children().find('span').first().text()).toBe(
      "/tmp/testplan/basic-test/mtest/scratch/4ac48da114046bd1246631bc1feb04c4"
    )
    expect(shallowComponent.find(Typography).first().children().find('span').last().text()).toBe(
      "3 files"
    )
    expect(shallowComponent.find('a').first().props().href).toBe(
      "/api/v1/reports/123/attachments/4ac48da114046bd1246631bc1feb04c4/index.html"
    )
    expect(shallowComponent.find('a').first().props().target).toBe("_blank")
    expect(shallowComponent.find('a').last().props().href).toBe(
      "/api/v1/reports/123/attachments/4ac48da114046bd1246631bc1feb04c4/subdir/module.py"
    )
    expect(shallowComponent.find('a').last().props().download).toBe("module.py")
    expect(shallowComponent).toMatchSnapshot();
  });

});