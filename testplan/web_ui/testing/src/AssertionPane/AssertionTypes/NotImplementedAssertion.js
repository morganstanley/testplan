import { Fragment } from "react";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFrown } from "@fortawesome/free-solid-svg-icons";

import { css, StyleSheet } from "aphrodite";

library.add(faFrown);

/**
 * Component that is rendered when there is no defined rendering mechanism for
 * the given assertion.
 */
function NotImplementedAssertion() {

  return (
    <Fragment>
      <FontAwesomeIcon
        size="lg"
        key="faFrown"
        icon="frown"
        className={css(styles.icon)}
      />
      Currently there is no rendering mechanism for this type of assertion.
      Please contact <strong>the developers</strong> if you would like to have
      it implemented.
    </Fragment>
  );
}

const styles = StyleSheet.create({
  icon: {
    margin: "0rem .5rem 0rem 0rem",
  },
});

export default NotImplementedAssertion;
