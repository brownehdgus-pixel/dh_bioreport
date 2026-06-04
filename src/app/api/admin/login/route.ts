import { NextResponse } from "next/server";
import {
  ADMIN_SESSION_COOKIE,
  createSessionToken,
  getAdminPassword,
  isAdminPasswordConfigured,
  verifyPassword,
} from "@/lib/adminAuth";

const SESSION_MAX_AGE = 60 * 60 * 24 * 7; // 7일

export async function POST(request: Request) {
  if (!isAdminPasswordConfigured()) {
    return NextResponse.json(
      {
        error:
          "서버에 비밀번호가 설정되어 있지 않습니다. ADMIN_PASSWORD 환경 변수를 등록해 주세요.",
      },
      { status: 500 }
    );
  }

  let body: { password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "요청 형식이 올바르지 않습니다." }, { status: 400 });
  }

  const password = body.password ?? "";
  if (!verifyPassword(password)) {
    return NextResponse.json(
      { error: "비밀번호가 올바르지 않습니다. 다시 입력해 주세요." },
      { status: 401 }
    );
  }

  const adminPassword = getAdminPassword()!;
  const token = createSessionToken(adminPassword);

  const response = NextResponse.json({ ok: true });
  response.cookies.set(ADMIN_SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });

  return response;
}
