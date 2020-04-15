import React from 'react';
import { css } from 'aphrodite';
import Table from 'reactstrap/lib/Table';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

/**
 * Get the metadata from the report and render it as a table.
 * @returns {React.FunctionComponentElement}
 */
export default function InfoTable() {
  const [ jsonReport ] = useReportState('app.reports.batch.jsonReport', false);
  return React.useMemo(() => {
    if(!(jsonReport && jsonReport.information)) {
      return (
        <table>
          <tbody>
          <tr>
            <td>No information to display.</td>
          </tr>
          </tbody>
        </table>
      );
    }
    const infoList = jsonReport.information.map((item, i) => (
      <tr key={`${i}`}>
        <td className={css(navStyles.infoTableKey)}>{item[0]}</td>
        <td className={css(navStyles.infoTableValue)}>{item[1]}</td>
      </tr>
    ));
    if(jsonReport.timer && jsonReport.timer.run) {
      if(jsonReport.timer.run.start) {
        infoList.push(
          <tr key='start'>
            <td>start</td>
            <td>{jsonReport.timer.run.start}</td>
          </tr>,
        );
      }
      if(jsonReport.timer.run.end) {
        infoList.push(
          <tr key='end'>
            <td>end</td>
            <td>{jsonReport.timer.run.end}</td>
          </tr>,
        );
      }
    }
    return (
      <Table bordered responsive={true} className={css(navStyles.infoTable)}>
        <tbody>
          {infoList}
        </tbody>
      </Table>
    );
  }, [ jsonReport ]);
}
