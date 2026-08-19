import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';
import { api } from '../services/apis';

vi.mock('../services/apis', () => ({
    api: {
        getCurrentUser: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
    },
}));

function AuthControls() {
    const { user, openLogin, logout } = useAuth();
    return (
        <div>
            <span>{user?.display_name || 'Anonymous'}</span>
            <button onClick={openLogin}>Open login</button>
            <button onClick={logout}>Log out</button>
        </div>
    );
}

describe('AuthProvider', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        api.getCurrentUser.mockResolvedValue(null);
        api.logout.mockResolvedValue();
    });

    it('shows the testing disclaimer and signs in without browser storage', async () => {
        api.login.mockResolvedValue({
            id: 'user-1',
            username: 'caine',
            display_name: 'Caine',
        });
        render(<AuthProvider><AuthControls /></AuthProvider>);

        fireEvent.click(screen.getByRole('button', { name: 'Open login' }));
        expect(screen.getByText(/Testing access only/)).toBeInTheDocument();
        expect(screen.getByText(/Full user authentication is not yet live/)).toBeInTheDocument();

        fireEvent.change(screen.getByLabelText('Username'), {
            target: { value: 'caine' },
        });
        fireEvent.change(screen.getByLabelText('Shared testing password'), {
            target: { value: 'shared-secret' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

        await waitFor(() => expect(api.login).toHaveBeenCalledWith(
            'caine', 'shared-secret'
        ));
        expect(await screen.findByText('Caine')).toBeInTheDocument();
    });
});
