import { authApiHandler } from '@neondatabase/auth/next/server';

// Force dynamic to prevent build-time execution
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

// Lazy initialization to avoid build-time env var check
let handler: ReturnType<typeof authApiHandler> | null = null;

function getHandler() {
  if (!handler) {
    handler = authApiHandler();
  }
  return handler;
}

export const GET = (...args: Parameters<ReturnType<typeof authApiHandler>['GET']>) =>
  getHandler().GET(...args);

export const POST = (...args: Parameters<ReturnType<typeof authApiHandler>['POST']>) =>
  getHandler().POST(...args);
