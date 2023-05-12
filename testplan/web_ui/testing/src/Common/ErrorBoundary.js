import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  };

  static getDerivedStateFromError(error) {
    return { error: error };
  }

  componentDidCatch(error, info) {
    this.logErrorToServices(error, info.componentStack);
  }

  // A fake logging service.
  logErrorToServices = console.log;

  render() {
    if (this.state.error) {
      return (
        <>
          <p style={{ color: 'red'}}>
            An error occurred while rendering component: "{this.props.children.type.name}"
          </p>
          <pre style={{ color: 'red'}}>{this.state.error.message}</pre>
        </>
      );
    }
    return this.props.children;
  }
}

export {ErrorBoundary};
