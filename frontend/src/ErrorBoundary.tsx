import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="w-screen h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center font-sans">
          <div className="backdrop-blur-xl bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-lg shadow-2xl">
            <h1 className="text-xl font-bold tracking-widest uppercase text-red-400 mb-4 border-b border-slate-800 pb-4">
              STORMFUSION AI
            </h1>
            <p className="text-slate-300 text-sm mb-4">
              Something went wrong while loading this view.
            </p>
            <div className="bg-slate-950 p-4 rounded-lg font-mono text-xs text-red-300 overflow-auto mb-6 max-h-32">
              {this.state.error?.toString()}
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors"
              >
                Reload View
              </button>
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  window.location.hash = ''; // Optional, if they used hash routing
                }}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors text-slate-300"
              >
                Return to Overview
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
