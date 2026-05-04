import { useCallback, useEffect, useState } from "react";
import { getErrorMessage } from "../lib/api/client";

interface UseApiQueryOptions<T> {
  enabled?: boolean;
  initialData?: T;
}

export function useApiQuery<T>(
  queryFn: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[],
  options: UseApiQueryOptions<T> = {}
) {
  const { enabled = true, initialData } = options;
  const [data, setData] = useState<T | undefined>(initialData);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    setLoading(true);
    setError(null);

    queryFn(controller.signal)
      .then((result) => {
        setData(result);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) {
          return;
        }

        setError(getErrorMessage(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [enabled, queryFn, reloadKey, ...deps]);

  return {
    data,
    error,
    loading,
    reload,
    setData,
  };
}
