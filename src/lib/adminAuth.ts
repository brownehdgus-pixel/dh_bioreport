import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

export const ADMIN_SESSION_COOKIE = "admin_session";

const SESSION_SALT = "bio-news-admin-v1";

export function getAdminPassword(): string | undefined {
  return process.env.ADMIN_PASSWORD;
}

export function isAdminPasswordConfigured(): boolean {
  const password = getAdminPassword();
  return Boolean(password && password.length > 0);
}

export function createSessionToken(password: string): string {
  return createHmac("sha256", password).update(SESSION_SALT).digest("hex");
}

export function verifyPassword(input: string): boolean {
  const expected = getAdminPassword();
  if (!expected) return false;

  const inputBuf = Buffer.from(input);
  const expectedBuf = Buffer.from(expected);
  if (inputBuf.length !== expectedBuf.length) return false;

  return timingSafeEqual(inputBuf, expectedBuf);
}

export function verifySessionToken(token: string | undefined): boolean {
  const password = getAdminPassword();
  if (!password || !token) return false;

  const expected = createSessionToken(password);
  const a = Buffer.from(token);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;

  return timingSafeEqual(a, b);
}

export async function isAdminAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  const token = cookieStore.get(ADMIN_SESSION_COOKIE)?.value;
  return verifySessionToken(token);
}
