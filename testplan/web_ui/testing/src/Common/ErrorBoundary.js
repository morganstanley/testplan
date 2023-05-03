import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    this.logErrorToServices(error, info.componentStack);
  }

  // A fake logging service.
  logErrorToServices = console.log;

  render() {
    if (this.shasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
} //<plaintext>{this.state.errorMessage}</plaintext>

const FallbackComponent = ({ error, resetErrorBoundary }) => {
  return (
    <>
      <p style={{ backgroundColor: 'red', color: 'white'}}>
        An Error Occurred while loading content!
      </p>
      <pre>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Try again</button>
    </>
  );
};
//      <button onClick={resetErrorBoundary}>Try again</button>

export {ErrorBoundary, FallbackComponent};
