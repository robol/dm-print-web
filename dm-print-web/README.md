# WebPrint frontend

This React frontend is built with [Vite](https://vite.dev/).

## Available scripts

Install dependencies with `npm install`, then use:

- `npm run dev` starts the development server at
  [http://localhost:3000](http://localhost:3000). Requests to `/getPrinters`
  and `/printFile`, along with authentication routes, are proxied to the Flask server at
  [http://localhost:5000](http://localhost:5000).
- `npm start` is an alias for `npm run dev`.
- `npm test` runs the Vitest test suite once.
- `npm run test:watch` runs tests in watch mode.
- `npm run build` creates the production bundle in `build/`.
- `npm run preview` serves the production bundle locally for inspection.

The output directory intentionally remains `build/` because the Flask
application and Docker image already serve files from that path.
