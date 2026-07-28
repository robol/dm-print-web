import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import App from './App';

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
    if (url === '/userinfo') {
      return {
        ok: true,
        json: async () => ({
          user: { id: '123', name: 'Test User', email: 'user@example.com' },
        }),
      };
    }

    return {
      ok: true,
      json: async () => ({ printers: [], stale: false }),
    };
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test('checks authentication before rendering the printer list', async () => {
  render(<App />);
  expect(await screen.findByRole('heading', { name: 'WebPrint' })).toBeInTheDocument();
  expect(await screen.findByText('Available printers')).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith('/userinfo', { credentials: 'include' });
  expect(fetch).toHaveBeenCalledWith('/getPrinters', { credentials: 'include' });
});
