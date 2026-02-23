"use client";

import { useState, FormEvent, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  getStoredUser,
  clearSession,
  apiUpdateProfile,
  apiGetMe,
  saveSession,
  getToken,
  AuthUser,
} from "@/lib/auth";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [fullName, setFullName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      const { ensureSession } = await import("@/lib/auth");
      await ensureSession();
      const stored = getStoredUser();
      if (!stored) return;
      setUser(stored);
      setFullName(stored.full_name);
      // Refresh from server
      apiGetMe()
        .then((fresh) => {
          setUser(fresh);
          setFullName(fresh.full_name);
        })
        .catch(() => {});
    })();
  }, []);

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setSaving(true);
    try {
      const payload: {
        full_name?: string;
        current_password?: string;
        new_password?: string;
      } = {};
      if (fullName.trim() !== user?.full_name)
        payload.full_name = fullName.trim();
      if (newPassword) {
        if (!currentPassword) {
          setError("Enter current password to set a new one");
          setSaving(false);
          return;
        }
        if (newPassword.length < 8) {
          setError("New password must be at least 8 characters");
          setSaving(false);
          return;
        }
        payload.current_password = currentPassword;
        payload.new_password = newPassword;
      }
      if (Object.keys(payload).length === 0) {
        setSaving(false);
        return;
      }
      const updated = await apiUpdateProfile(payload);
      setUser(updated);
      setFullName(updated.full_name);
      setCurrentPassword("");
      setNewPassword("");
      // Update stored user
      const token = getToken()!;
      saveSession({ access_token: token, token_type: "bearer", user: updated });
      setSuccessMsg("Profile updated");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSaving(false);
    }
  }

  function handleLogout() {
    clearSession();
    document.cookie = "sc_onboarded=; path=/; max-age=0";
    router.push("/onboard");
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-8 border-2 border-zinc-800 border-t-indigo-500 rounded-full animate-spin" />
        <p className="text-xs text-zinc-600">Loading profile…</p>
      </div>
    );
  }

  const initials = user.full_name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Nav */}
      <header className="border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <Link href="/" className="text-zinc-100 font-bold tracking-tight hover:text-indigo-400 transition-colors">
              SentriChain
            </Link>
            <span className="text-zinc-700">/</span>
            <span className="text-zinc-500 text-sm">Profile</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard"
              className="flex items-center gap-2 text-sm px-3.5 py-2 rounded-xl border border-zinc-800 text-zinc-400 hover:text-zinc-100 hover:border-zinc-600 bg-zinc-900/50 transition-all">
              ← Dashboard
            </Link>
            <button onClick={handleLogout}
              className="text-sm px-3.5 py-2 rounded-xl border border-zinc-800 text-zinc-500 hover:text-red-400 hover:border-red-500/30 bg-zinc-900/50 transition-all">
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left column — identity */}
          <div className="lg:col-span-1">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 text-center">
              <div className="w-20 h-20 rounded-2xl bg-linear-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-2xl select-none mx-auto mb-4">
                {initials}
              </div>
              <p className="text-zinc-100 font-semibold text-lg">{user.full_name}</p>
              <p className="text-zinc-500 text-sm mt-1">{user.email}</p>
              <span className={`mt-3 inline-block text-xs px-3 py-1 rounded-full font-semibold border ${
                user.role === "admin"
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                  : "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
              }`}>
                {user.role}
              </span>

              <div className="mt-6 pt-6 border-t border-zinc-800 space-y-3 text-left">
                {[
                  { label: "Account ID", value: `#${user.id}`, mono: true },
                  { label: "Member since", value: new Date(user.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }), mono: false },
                ].map(({ label, value, mono }) => (
                  <div key={label} className="flex justify-between items-baseline gap-2">
                    <span className="text-zinc-500 text-xs">{label}</span>
                    <span className={`text-zinc-300 text-sm ${mono ? "font-mono" : ""}`}>{value}</span>
                  </div>
                ))}
              </div>

              <div className="mt-6 space-y-2">
                <Link href="/onboard"
                  className="block w-full text-center text-sm py-2.5 rounded-xl bg-indigo-600/10 border border-indigo-600/20 text-indigo-400 hover:bg-indigo-600/20 hover:text-indigo-300 transition-all">
                  Update company profile
                </Link>
                <button onClick={handleLogout}
                  className="block w-full text-center text-sm py-2.5 rounded-xl text-zinc-600 hover:text-red-400 transition-colors">
                  Sign out of all sessions
                </button>
              </div>
            </div>
          </div>

          {/* Right column — edit form */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
              <h2 className="text-lg font-semibold text-zinc-100 mb-6">Edit profile</h2>

              {successMsg && (
                <div className="mb-5 flex items-center gap-3 p-4 rounded-xl bg-emerald-500/8 border border-emerald-500/25 text-emerald-400 text-sm">
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  {successMsg}
                </div>
              )}
              {error && (
                <div className="mb-5 flex items-center gap-3 p-4 rounded-xl bg-red-500/8 border border-red-500/25 text-red-400 text-sm">
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  {error}
                </div>
              )}

              <form onSubmit={handleSave} className="space-y-5">
                <div>
                  <label htmlFor="full-name" className="block text-sm font-medium text-zinc-400 mb-2">Full name</label>
                  <input
                    id="full-name"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 text-sm
                               focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 transition-all"
                  />
                </div>

                <div className="border-t border-zinc-800 pt-5">
                  <h3 className="text-sm font-medium text-zinc-400 mb-4">Change password</h3>
                  <div className="space-y-3">
                    <input
                      type="password"
                      placeholder="Current password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 text-sm
                                 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 transition-all"
                    />
                    <input
                      type="password"
                      placeholder="New password (min 8 characters)"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 text-sm
                                 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl px-6 py-3 transition-all"
                >
                  {saving && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                  {saving ? "Saving…" : "Save changes"}
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
