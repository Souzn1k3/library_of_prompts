"use client";

import { useEffect, useRef, useState } from "react";

export function useLmnBalanceFeedback(balance: number | null | undefined) {
  const previousBalanceRef = useRef<number | null>(null);
  const [change, setChange] = useState<"up" | "down" | null>(null);
  const [delta, setDelta] = useState<number | null>(null);

  useEffect(() => {
    if (balance === null || balance === undefined) {
      previousBalanceRef.current = null;
      setChange(null);
      setDelta(null);
      return;
    }

    if (previousBalanceRef.current === null) {
      previousBalanceRef.current = balance;
      return;
    }

    const nextDelta = balance - previousBalanceRef.current;
    previousBalanceRef.current = balance;

    if (nextDelta === 0) {
      return;
    }

    setChange(nextDelta > 0 ? "up" : "down");
    setDelta(nextDelta);

    const timeoutId = window.setTimeout(() => {
      setChange(null);
      setDelta(null);
    }, 1200);

    return () => window.clearTimeout(timeoutId);
  }, [balance]);

  return { change, delta };
}
