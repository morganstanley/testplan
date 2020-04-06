import React from "react";
import { Route, Switch, Redirect } from "react-router-dom";

/**
 * We use "strict" here to ensure that paths end with a trailing slash. This
 * makes the UI-rendered hash routes more distinguishable from the
 * server-rendered regular routes. The final <Route> catches URLs entered by
 * the user that don't contain a trailing slash, e.g. "/:url", and redirects
 * them to e.g. "/:url/".
 */
export default ({ children = null, location = null }) => (
    <Switch location={location}>
      {/* Must be first - require trailing slash */}
      <Route strict exact sensitive from=':pathNoSlash(|.*?[^/])'
             component={routeProps => (
               <Redirect to={{
                 ...routeProps.location,
                 pathname: `${routeProps.location.pathname}/`
               }} />
             )}
      />
      {children}
    </Switch>
);
