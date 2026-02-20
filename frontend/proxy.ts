import { NextRequest, NextResponse } from "next/server";

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const isOnboarded = req.cookies.get("sc_onboarded")?.value === "1";

  // Redirect old auth pages to onboard
  if (pathname.startsWith("/login") || pathname.startsWith("/signup")) {
    return NextResponse.redirect(
      new URL(isOnboarded ? "/dashboard" : "/onboard", req.url),
    );
  }

  // Ensure /dashboard is only reachable after onboarding
  if (!isOnboarded && pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/onboard", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api).*)"],
};

