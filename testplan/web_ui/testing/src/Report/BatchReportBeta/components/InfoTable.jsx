import React from 'react';
import { css } from 'aphrodite';
import { Table } from 'reactstrap';
import { connect } from 'react-redux';
import { mkGetReportDocument } from '../state/reportSelectors';
import navStyles from '../../../Toolbar/navStyles';

const INFO_TABLE_CLASSES = css(navStyles.infoTable);
const INFO_TABLE_KEY_CLASSES = css(navStyles.infoTableKey);
const INFO_TABLE_VAL_CLASSES = css(navStyles.infoTableValue);

const connector = connect(
  () => {
    const getReportDocument = mkGetReportDocument();
    return function mapStateToProps(state) {
      return {
        reportDocument: getReportDocument(state),
      };
    };
  },
);

const InfoTable = ({ reportDocument }) => React.useMemo(() => {
  if(!(reportDocument && reportDocument.information)) {
    return (
      <table>
        <tbody><tr><td>No information to display.</td></tr></tbody>
      </table>
    );
  }
  const infoList = reportDocument.information.map((item, i) => (
    <tr key={`${i}`}>
      <td className={INFO_TABLE_KEY_CLASSES}>{item[0]}</td>
      <td className={INFO_TABLE_VAL_CLASSES}>{item[1]}</td>
    </tr>
  ));
  if(reportDocument.timer && reportDocument.timer.run) {
    if(reportDocument.timer.run.start) {
      infoList.push(
        <tr key='start'>
          <td>start</td>
          <td>{reportDocument.timer.run.start}</td>
        </tr>,
      );
    }
    if(reportDocument.timer.run.end) {
      infoList.push(
        <tr key='end'>
          <td>end</td>
          <td>{reportDocument.timer.run.end}</td>
        </tr>,
      );
    }
  }
  return (
    <Table bordered responsive={true} className={INFO_TABLE_CLASSES}>
      <tbody>{infoList}</tbody>
    </Table>
  );
}, [ reportDocument ]);

export default connector(InfoTable);
