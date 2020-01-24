import React from 'react';
import PropTypes from 'prop-types';


const DescriptionPane = (props) => {
    let description = null;
    if (props.descriptionEntries && props.descriptionEntries.length !== 0) {
        description = props.descriptionEntries.map((element, index) => {
            return (
                <div key={'descriptionDiv'+index}>
                    <pre key={'descriptionPre'+index}>
                        {element}
                    </pre>
                </div>
            );
        });
    }
    
    return (
        <div className='description'>
            {description}
        </div>
    );
};

DescriptionPane.propTypes = {
    /** Selected entries' description list to be displayed */
    descriptionEntries: PropTypes.arrayOf(PropTypes.string),
};


    
export default DescriptionPane;
