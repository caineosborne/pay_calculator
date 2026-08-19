import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../services/apis';

const anonymousAuth = {
    user: null,
    isLoading: false,
    openLogin: () => {},
    closeLogin: () => {},
    logout: async () => {},
};
const AuthContext = createContext(anonymousAuth);

function LoginDialog({ isOpen, onClose, onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (!isOpen) {
            setPassword('');
            setMessage('');
        }
    }, [isOpen]);

    if (!isOpen) {
        return null;
    }

    const submit = async (event) => {
        event.preventDefault();
        setIsSubmitting(true);
        setMessage('');
        try {
            await onLogin(username, password);
            setPassword('');
            onClose();
        } catch (error) {
            setMessage(error.message);
        } finally {
            setPassword('');
            setIsSubmitting(false);
        }
    };

    return (
        <div className="disclaimer-backdrop" role="presentation">
            <section
                className="auth-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="auth-dialog-title"
            >
                <p className="eyebrow">Private rule storage</p>
                <h2 id="auth-dialog-title">Sign in to save</h2>
                <p className="auth-testing-notice">
                    <strong>Testing access only.</strong> These named accounts use a
                    shared password and are intended only for controlled testing.
                    Full user authentication is not yet live. Do not use these
                    accounts for sensitive or production data.
                </p>
                <form onSubmit={submit} className="auth-form">
                    <label>
                        Username
                        <input
                            name="username"
                            autoComplete="username"
                            value={username}
                            onChange={(event) => setUsername(event.target.value)}
                            required
                            autoFocus
                        />
                    </label>
                    <label>
                        Shared testing password
                        <input
                            name="password"
                            type="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            required
                        />
                    </label>
                    {message && <p className="auth-error" role="alert">{message}</p>}
                    <div className="auth-actions">
                        <button type="button" className="pay-button" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="pay-button auth-submit" disabled={isSubmitting}>
                            {isSubmitting ? 'Signing in…' : 'Sign in'}
                        </button>
                    </div>
                </form>
            </section>
        </div>
    );
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoginOpen, setIsLoginOpen] = useState(false);

    useEffect(() => {
        let isMounted = true;
        api.getCurrentUser()
            .then((currentUser) => {
                if (isMounted) setUser(currentUser);
            })
            .catch(() => {
                if (isMounted) setUser(null);
            })
            .finally(() => {
                if (isMounted) setIsLoading(false);
            });
        return () => {
            isMounted = false;
        };
    }, []);

    const value = useMemo(() => ({
        user,
        isLoading,
        openLogin: () => setIsLoginOpen(true),
        closeLogin: () => setIsLoginOpen(false),
        login: async (username, password) => {
            const signedInUser = await api.login(username, password);
            setUser(signedInUser);
            return signedInUser;
        },
        logout: async () => {
            await api.logout();
            setUser(null);
        },
    }), [user, isLoading]);

    return (
        <AuthContext.Provider value={value}>
            {children}
            <LoginDialog
                isOpen={isLoginOpen}
                onClose={() => setIsLoginOpen(false)}
                onLogin={value.login}
            />
        </AuthContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
