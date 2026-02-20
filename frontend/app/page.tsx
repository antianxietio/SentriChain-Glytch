"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ensureSession } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      await ensureSession();
      const onboarded = document.cookie
        .split(";").some((c) => c.trim().startsWith("sc_onboarded=1"));
      router.replace(onboarded ? "/dashboard" : "/onboard");
    })();
  }, [router]);

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <div className="w-5 h-5 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" />
    </div>
  );
}
