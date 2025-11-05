import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const OAuthCallback: React.FC = () => {
    const { handleDiscordCallback } = useAuth();
    const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
    const [error, setError] = useState<string>('');

    useEffect(() => {
        let isMounted = true;
        
        const processCallback = async () => {
            // Get the code from URL parameters
            const params = new URLSearchParams(window.location.search);
            const code = params.get('code');
            const errorParam = params.get('error');

            if (errorParam) {
                if (isMounted) {
                    setStatus('error');
                    setError('Authorization was denied or cancelled');
                }
                return;
            }

            if (!code) {
                if (isMounted) {
                    setStatus('error');
                    setError('No authorization code received');
                }
                return;
            }

            try {
                const success = await handleDiscordCallback(code);
                if (!isMounted) return;
                
                if (success) {
                    setStatus('success');
                    // Immediate redirect - no delay
                    window.location.replace('/');
                } else {
                    setStatus('error');
                    setError('Access denied. You must have the Staff role or an authorized role to access this dashboard.');
                }
            } catch (err) {
                if (!isMounted) return;
                setStatus('error');
                setError('An unexpected error occurred during authentication');
                console.error('OAuth callback error:', err);
            }
        };

        processCallback();
        
        return () => {
            isMounted = false;
        };
    }, [handleDiscordCallback]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-900">
            <div className="bg-gray-800 p-10 rounded-2xl shadow-2xl w-full max-w-md border border-gray-700">
                <div className="text-center">
                    {status === 'processing' && (
                        <>
                            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full mb-4 animate-pulse">
                                <svg className="w-10 h-10 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">Authenticating...</h2>
                            <p className="text-gray-400">Please wait while we verify your Discord account</p>
                        </>
                    )}

                    {status === 'success' && (
                        <>
                            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full mb-4">
                                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">Success!</h2>
                            <p className="text-gray-400">Redirecting to dashboard...</p>
                        </>
                    )}

                    {status === 'error' && (
                        <>
                            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-red-500 to-pink-500 rounded-full mb-4">
                                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">Authentication Failed</h2>
                            <p className="text-red-300 mb-4">{error}</p>
                            <button
                                onClick={() => window.location.href = '/'}
                                className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-6 rounded-lg transition-colors"
                            >
                                Return to Login
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OAuthCallback;

