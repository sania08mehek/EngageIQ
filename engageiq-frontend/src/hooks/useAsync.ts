import { useCallback, useEffect, useState } from 'react';

interface Settled<T> {
  key: string;
  data?: T;
  error?: string;
}

/** Loads data when `deps` change. `reload()` fetches again and keeps the old data on screen meanwhile. */
export function useAsync<T>(load: () => Promise<T>, deps: unknown[]) {
  const key = JSON.stringify(deps);
  const [settled, setSettled] = useState<Settled<T> | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    load()
      .then((data) => alive && setSettled({ key, data }))
      .catch((e: unknown) =>
        alive && setSettled({ key, error: e instanceof Error ? e.message : 'Something went wrong.' }),
      );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick]);

  const current = settled && settled.key === key ? settled : null;
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data: current?.data, error: current?.error, loading: !current, reload };
}
