import { useEffect, useState } from "react";
import { getProducts } from "../api/productsApi";

export function useProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    async function loadProducts() {
      try {
        setLoading(true);
        setError(null);
        const data = await getProducts();
        if (!active) return;
        setProducts(data ?? []);
        if (data == null) {
          setError(new Error("Resposta inesperada da API de produtos. Verifique a configuracao da URL do backend."));
        }
      } catch (err) {
        if (active) setError(err);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadProducts();

    return () => {
      active = false;
    };
  }, []);

  return { products, loading, error };
}
