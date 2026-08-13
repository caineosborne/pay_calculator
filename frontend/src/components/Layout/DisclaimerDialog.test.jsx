import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DisclaimerDialog } from './DisclaimerDialog';

vi.mock('../../context/PayContext', () => ({
    usePay: () => ({ state: { config: { award: 'fast_food' } } }),
}));

vi.mock('../../services/apis', () => ({
    api: {
        getDisclaimers: vi.fn().mockResolvedValue({
            generic: {
                title: 'Important disclaimer',
                paragraphs: ['Indicative estimate only.'],
            },
            awards: {
                fast_food: {
                    title: 'Scope and assumptions',
                    paragraphs: ['Selected Fast Food Award rules are modelled.'],
                    assumptions: ['The selected classification is correct.'],
                    limitations: ['Some entitlements are not calculated.'],
                    closing_paragraphs: ['Check the applicable records.'],
                },
            },
        }),
    },
}));

describe('DisclaimerDialog', () => {
    it('shows both the generic and selected award limitations', async () => {
        const onClose = vi.fn();
        render(<DisclaimerDialog isOpen onClose={onClose} />);

        expect(await screen.findByText('Indicative estimate only.')).toBeInTheDocument();
        expect(screen.getByText('Scope and assumptions')).toBeInTheDocument();
        expect(screen.getByText('Assumptions')).toBeInTheDocument();
        expect(screen.getByText('The selected classification is correct.')).toBeInTheDocument();
        expect(screen.getByText('Limitations')).toBeInTheDocument();
        expect(screen.getByText('Some entitlements are not calculated.')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'I understand' }));
        expect(onClose).toHaveBeenCalledTimes(1);
    });
});
