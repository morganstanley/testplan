import React from 'react';
import PropTypes from 'prop-types';
import {StyleSheet, css} from "aphrodite";


const LogGroup = (props) => {
    if (props.logs && props.logs.length !== 0) {
        const logInfos = props.logs.map(element => {
            return (
                <div key={element.uid}>
                    <pre className={css(styles.logEntry)}>
                        {element.message}
                    </pre>
                </div>
            );
        });
        return (
            <div className="LogGroup">
                {logInfos}
            </div>
        );
    } else {
        return null;
    }
};

LogGroup.propTypes = {
    /** Log list entries to be displayed */
    logs: PropTypes.arrayOf(PropTypes.object),
};


const styles = StyleSheet.create({
    logEntry: {
        color: 'red',
    },
});
    
export default LogGroup;
