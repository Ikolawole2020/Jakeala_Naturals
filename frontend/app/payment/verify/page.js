"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { naira, verifyPayment } from "@/lib/api";

/**
 * Where Paystack sends the shopper back to.
 *
 * The browser callback is only a convenience - it confirms with Paystack so the
 * customer sees an outcome straight away. The webhook is the source of truth and
 * may settle the order first, in which case this page says so rather than
 * double-charging or erroring.
 */
function VerifyInner({ searchParams }) {
  const reference = searchParams?.get("reference") || "";
  const orderId = searchParams?.get("order_id") || "";
  const [state, setState] = useState("checking");
  const [order, setOrder] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!reference) {
      setState("failed");
      setMessage("That payment link is missing its reference.");
      return;
    }
    verifyPayment({ reference, order_id: orderId })
      .then((data) => {
        setOrder(data.order || null);
        setState(data.settled ? "paid" : "failed");
      })
      .catch((err) => {
        setMessage(readError(err));
        setState("failed");
      });
  }, [reference, orderId]);

  const copy = {
    checking: {
      kicker: "Payment",
      title: "Confirming your payment…",
      body: "Hold on while we check with Paystack. This takes a few seconds.",
    },
    paid: {
      kicker: "Thank you",
      title: "Payment received",
      body: "Your order is confirmed and a receipt is on its way to your inbox.",
    },
    failed: {
      kicker: "Payment",
      title: "We could not confirm that payment",
      body: "No money has left your account. Your basket is untouched, so you can try again.",
    },
  }[state];

  return (
    <div className="wrap page-hero" style={{ maxWidth: 620, textAlign: "center" }}>
      <p className="kicker">{copy.kicker}</p>
      <h1 className="serif" style={{ fontSize: 40, margin: "8px 0 14px" }}>
        {copy.title}
      </h1>
      <p className="muted">{copy.body}</p>

      {message && <p className="alert error" style={{ marginTop: 16 }}>{message}</p>}

      {order && (
        <div className="buybox" style={{ marginTop: 22, textAlign: "left" }}>
          <p style={{ margin: "0 0 6px" }}>
            <strong>Order #{order.id}</strong>
            {order.payment_reference && ` · ${order.payment_reference}`}
          </p>
          <p className="muted" style={{ margin: "0 0 6px" }}>
            {order.full_name} · {order.city}, {order.state}
          </p>
          <div className="price">Total {naira(order.total)}</div>
        </div>
      )}

      <div style={{ marginTop: 26, display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
        <Link className="btn btn-primary" href="/account">
          Track my order
        </Link>
        <Link className="btn btn-ghost" href="/shop">
          Continue shopping
        </Link>
      </div>
    </div>
  );
}

export default function VerifyPage({ searchParams }) {
  return (
    <Suspense fallback={null}>
      <VerifyInner searchParams={searchParams} />
    </Suspense>
  );
}

function readError(err) {
  try {
    const body = JSON.parse(err.message);
    if (typeof body === "string") return body;
    if (body.detail) return body.detail;
    return Object.values(body).flat().join(" ");
  } catch {
    return "Something went wrong confirming the payment.";
  }
}