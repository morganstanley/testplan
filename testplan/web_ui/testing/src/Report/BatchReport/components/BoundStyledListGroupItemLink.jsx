import React from 'react';
import { useRouteMatch } from 'react-router-dom';

import useReportState from '../hooks/useReportState';
import { BOTTOMMOST_ENTRY_CATEGORY } from '../../../Common/defaults';
import { uriComponentCodec } from '../utils';
import StyledListGroupItemLink from './StyledListGroupItemLink';
import TagList from '../../../Nav/TagList';
import NavEntry from '../../../Nav/NavEntry';

export default ({ entry, idx, nPass, nFail }) => {
  const { url } = useRouteMatch(),
    { name, status, category, tags, uid } = entry,
    [ isShowTags, [ setUriHashPathComponentAlias, setSelectedTestCase ] ] =
      useReportState(
        'app.reports.batch.isShowTags',
        [ 'setUriHashPathComponentAlias', 'setAppBatchReportSelectedTestCase' ],
      ),
    isBottommost = category === BOTTOMMOST_ENTRY_CATEGORY,
    encodedName = uriComponentCodec.encode(name),
    nextPathname = isBottommost ? url : `${url}/${encodedName}`,
    onClickOverride = !isBottommost ? {
      onClick() { setSelectedTestCase(null); },
    } : {
      onClick(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        setSelectedTestCase(entry);
      },
    };
  setUriHashPathComponentAlias(encodedName, name);
  return (
    <StyledListGroupItemLink key={uid}
                             dataUid={uid}
                             tabIndex={`${idx + 1}`}
                             pathname={nextPathname}
                             {...onClickOverride}
    >
      {isShowTags && tags ? <TagList entryName={name} tags={tags}/> : null}
      <NavEntry caseCountPassed={nPass}
                caseCountFailed={nFail}
                type={category}
                status={status}
                name={name}
      />
    </StyledListGroupItemLink>
  );
};
