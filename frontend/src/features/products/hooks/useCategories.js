import { useEffect, useState } from "react";
import { getCategories } from "../api/productsApi";

export function useCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    async function loadCategories() {
      try {
        setLoading(true);
        setError(null);
        const data = await getCategories();
        if (active) setCategories(data ?? []);
      } catch (err) {
        if (active) setError(err);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadCategories();

    return () => {
      active = false;
    };
  }, []);

  return { categories, loading, error };
}
