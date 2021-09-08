import React from 'react';
import PropTypes from 'prop-types';
import {StyleSheet, css} from "aphrodite";
import {RED, ORANGE, BLACK, LOG_TYPE} from '../Common/defaults.js'

function getLogColor(logType) {
    switch(logType) {
        case LOG_TYPE.error: return css(styles.logERROR);
        case LOG_TYPE.warning: return css(styles.logWARNING);
        default: return css(styles.logDEFAULT);
    }
}

const LogGroup = (props) => {
    if (props.logs && props.logs.length !== 0) {
        const logInfos = props.logs.map(element => {
            return (
                <div key={element.uid}>
                    <pre className={getLogColor(element.levelname)}>
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
    logERROR: {
        color: RED,
    },
    logWARNING: {
        color: ORANGE,
    },
    logDEFAULT: {
        color: BLACK,
    },
});

    
export default LogGroup;
