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
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" />
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
      <header className="border-b border-zinc-800 bg-zinc-900/60 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link
            href="/"
            className="text-zinc-100 font-semibold tracking-tight text-sm"
          >
            SentriChain
          </Link>
          <button
            onClick={handleLogout}
            className="text-zinc-400 hover:text-zinc-100 text-sm transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-6 py-12">
        {/* Avatar + identity */}
        <div className="flex items-center gap-4 mb-8">
          <div className="w-14 h-14 rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold text-lg select-none">
            {initials}
          </div>
          <div>
            <p className="text-zinc-100 font-semibold">{user.full_name}</p>
            <p className="text-zinc-400 text-sm">{user.email}</p>
            <span
              className={`mt-1 inline-block text-xs px-2 py-0.5 rounded-full font-medium ${
                user.role === "admin"
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
              }`}
            >
              {user.role}
            </span>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-zinc-100 font-semibold mb-5">Edit profile</h2>

          {successMsg && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm">
              {successMsg}
            </div>
          )}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm text-zinc-400 mb-1.5">
                Full name
              </label>
              <input
                id="full-name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2.5 text-zinc-100 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
            </div>

            <div className="border-t border-zinc-800 pt-4">
              <p className="text-xs text-zinc-500 mb-3 uppercase tracking-wide">
                Change password
              </p>
              <div className="space-y-3">
                <input
                  type="password"
                  placeholder="Current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2.5 text-zinc-100 text-sm placeholder-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
                <input
                  type="password"
                  placeholder="New password (min 8 chars)"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2.5 text-zinc-100 text-sm placeholder-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg px-4 py-2.5 transition-colors"
            >
              {saving ? "Saving..." : "Save changes"}
            </button>
          </form>
        </div>

        {/* Account meta */}
        <div className="mt-6 bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h3 className="text-zinc-400 text-xs uppercase tracking-wide mb-3">
            Account details
          </h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-zinc-500">Email</dt>
              <dd className="text-zinc-300 font-mono">{user.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-zinc-500">Role</dt>
              <dd className="text-zinc-300">{user.role}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-zinc-500">Account ID</dt>
              <dd className="text-zinc-300 font-mono">#{user.id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-zinc-500">Created</dt>
              <dd className="text-zinc-300">
                {new Date(user.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>

        <div className="mt-6 text-center">
          <button
            onClick={handleLogout}
            className="text-sm text-zinc-500 hover:text-red-400 transition-colors"
          >
            Sign out of all sessions
          </button>
        </div>
      </main>
    </div>
  );
}
