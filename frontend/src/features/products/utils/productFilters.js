export function filterProducts(products, { busca, categoria, faixaEtaria }) {
  const searchTerm = busca.trim().toLowerCase();

  return (products ?? []).filter(product => {
    const categoryName = product.categories?.[0]?.name?.toLowerCase() || "";
    const matchesSearch = [product.name, product.description, categoryName]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(searchTerm);
    const matchesCategory = categoria === "Todos" || (
      product.categories
        ? product.categories.some(item => item.slug === categoria)
        : false
    );
    const matchesAgeRange = faixaEtaria === "Todas" || product.age_range === faixaEtaria;

    return matchesSearch && matchesCategory && matchesAgeRange;
  });
}
