"use client";

import { useEffect, useState } from "react";
import {
  clearCustomerToken,
  customerToken,
  login,
  me,
  register,
  requestPasswordReset,
  setCustomerToken,
  verifyEmail,
} from "@/lib/api";
import Dashboard from "@/components/account/Dashboard";

/**
 * The signed-out view: sign in, create an account, or recover a password.
 *
 * Laid out as a two-column card - a brand panel on the left, the form on the
 * right - so the page reads as a deliberate destination rather than a bare
 * column of inputs. On narrow screens the brand panel collapses away and the
 * form takes the full width.
 */
function AuthPanel({ onSignedIn }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function set(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setError("");
    setMessage("");
  }

  function go(next) {
    setMode(next);
    setError("");
    setMessage("");
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (mode === "register") {
        const result = await register(form);
        setMessage(
          result.email_sent
            ? "Account created. Check your inbox and click the verification link to activate it."
            : "Account created, but the email could not be sent just now. Try again in a minute, or contact us."
        );
        setMode("login");
      } else if (mode === "forgot") {
        await requestPasswordReset({ email: form.email });
        // Deliberately the same wording whether or not the address has an
        // account, so this form cannot be used to discover who shops here.
        setMessage(
          "If that email address has an account, a reset link is on its way. It expires shortly."
        );
        setMode("login");
      } else {
        const data = await login({
          identifier: form.email,
          password: form.password,
        });
        onSignedIn(data);
      }
    } catch (err) {
      setError(readError(err));
    } finally {
      setBusy(false);
    }
  }

  const titles = {
    login: ["Sign in", "Welcome back. Your orders and saved addresses are waiting."],
    register: [
      "Create your account",
      "Track orders, save addresses and check out faster next time.",
    ],
    forgot: ["Reset your password", "We'll email you a secure link to choose a new one."],
  };
  const [title, subtitle] = titles[mode];

  return (
    <div className="auth">
      <aside className="auth-brand">
        <p className="kicker">Where every skin is our priority</p>
        <h2 className="serif">Care that begins at the root.</h2>
        <p className="muted">
          Herbal teas and feminine care, made for skin that asks for patience. An
          account keeps your order history and delivery details in one place.
        </p>
        <ul className="auth-points">
          <li>Track every order from paid to delivered</li>
          <li>Save an address and check out in a few taps</li>
          <li>Email-only access, no social logins to keep track of</li>
        </ul>
      </aside>

      <div className="auth-form-wrap">
        <h1 className="serif">{title}</h1>
        <p className="muted" style={{ marginBottom: 22 }}>{subtitle}</p>

        <form className="form" onSubmit={submit}>
          {mode === "register" && (
            <label className="field">
              <span>Full name</span>
              <input
                placeholder="Ada Lovelace"
                autoComplete="name"
                required
                value={form.full_name}
                onChange={(e) => set("full_name", e.target.value)}
              />
            </label>
          )}

          <label className="field">
            <span>Email address</span>
            <input
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              required
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
            />
          </label>

          {mode !== "forgot" && (
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                placeholder="••••••••"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
                value={form.password}
                onChange={(e) => set("password", e.target.value)}
              />
            </label>
          )}

          {error && <p className="alert error" role="alert">{error}</p>}
          {message && <p className="alert" role="status">{message}</p>}

          <button className="btn btn-dark btn-block" disabled={busy}>
            {busy
              ? "Please wait…"
              : mode === "login"
              ? "Sign in"
              : mode === "register"
              ? "Create account"
              : "Send reset link"}
          </button>
        </form>

        <div className="auth-switch">
          {mode === "login" && (
            <>
              <button className="linkish" onClick={() => go("register")}>
                New here? Create an account
              </button>
              <button className="linkish" onClick={() => go("forgot")}>
                Forgot your password?
              </button>
            </>
          )}
          {mode !== "login" && (
            <button className="linkish" onClick={() => go("login")}>
              ← Back to sign in
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function readError(err) {
  try {
    const body = JSON.parse(err.message);
    if (typeof body === "string") return body;
    if (body.detail) return body.detail;
    return Object.values(body).flat().join(" ");
  } catch {
    return "Something went wrong. Please try again.";
  }
}


/**
 * /account - one route, two very different jobs.
 *
 * Signed out it renders the sign-in / register / reset panel. Signed in it
 * renders the customer dashboard. Keeping both behind a single route means the
 * verification link that lands here can finish the job and drop the customer
 * straight into their dashboard without a second redirect.
 */
export default function AccountPage() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState("");

  useEffect(() => {
    (async () => {
      const params = new URLSearchParams(window.location.search);
      const email = params.get("email");
      const code = params.get("code");
      const purpose = params.get("purpose");

      // A verification or password-reset link lands here with the code in the
      // query string. It is exchanged for a session, then the URL is scrubbed so
      // the token is not left sitting in history, bookmarks or a referrer header.
      if (email && code && (purpose === "verify" || purpose === "reset")) {
        setVerifying(true);
        try {
          const data = await verifyEmail({ email, code });
          setCustomerToken(data.token);
          setUser(data.user);
          window.history.replaceState({}, "", "/account");
        } catch (err) {
          setVerifyError(readError(err));
        } finally {
          setVerifying(false);
        }
        return;
      }

      if (customerToken()) {
        try {
          setUser(await me());
        } catch {
          // An expired or revoked token is cleared so the page falls back to the
          // sign-in form instead of looping on a broken session.
          clearCustomerToken();
        }
      }
      setChecking(false);
    })();
  }, []);

  function signedIn(data) {
    setCustomerToken(data.token);
    setUser(data.user);
  }

  function signOut() {
    clearCustomerToken();
    setUser(null);
  }

  if (checking || verifying) {
    return (
      <div className="wrap page-hero" style={{ maxWidth: 520, textAlign: "center" }}>
        <p className="kicker">Your account</p>
        <h1 className="serif">{verifying ? "Confirming your email…" : "Loading your account…"}</h1>
        <p className="muted">One moment while we check your session.</p>
      </div>
    );
  }

  if (verifyError) {
    return (
      <div className="wrap page-hero" style={{ maxWidth: 520 }}>
        <p className="kicker">Your account</p>
        <h1 className="serif">That link didn't work</h1>
        <p className="alert error" role="alert">{verifyError}</p>
        <p className="muted">
          Links are single-use and expire after a short while. Request a new one
          and try again.
        </p>
      </div>
    );
  }

  if (user) return <Dashboard user={user} onUserChange={setUser} onSignOut={signOut} />;

  return (
    <div className="wrap page-hero" style={{ paddingBottom: 72 }}>
      <AuthPanel onSignedIn={signedIn} />
    </div>
  );
}

