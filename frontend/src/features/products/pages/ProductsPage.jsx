import { useState } from "react";
import EmptyState from "@/shared/components/EmptyState";
import ErrorMessage from "@/shared/components/ErrorMessage";
import Hero from "@/shared/components/Hero";
import LoadingState from "@/shared/components/LoadingState";
import ProductCard from "../components/ProductCard";
import { useCategories } from "../hooks/useCategories";
import { useProducts } from "../hooks/useProducts";
import { filterProducts } from "../utils/productFilters";
import "../styles/ProductsPage.css";

export default function ProductsPage() {
  const [busca, setBusca] = useState("");
  const [categoria, setCategoria] = useState("Todos");
  const [faixaEtaria, setFaixaEtaria] = useState("Todas");

  const { products, loading, error } = useProducts();
  const { categories } = useCategories();
  const ageRanges = [...new Set((products ?? []).map((product) => product.age_range).filter(Boolean))];

  const produtosFiltrados = filterProducts(products, { busca, categoria, faixaEtaria });

  return (
    <>
      <Hero
        title="Produtos"
        subtitle="Encontre brinquedos e itens infantis para alugar pelo período ideal."
      />

    <main className="produtos-page">
      <section className="produtos-toolbar-card">
        <div className="produtos-toolbar-card__intro">
          <p className="produtos-toolbar-card__eyebrow">Catalogo</p>
          <h2>Encontre a opcao ideal para cada fase</h2>
          <span>Filtre por categoria, faixa etaria e acompanhe a disponibilidade antes de entrar no detalhe.</span>
        </div>

        <div className="produtos-toolbar">
          <input
            className="field-control"
            type="text"
            placeholder="Buscar produto, descricao ou categoria..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />

          <select className="field-control" value={categoria} onChange={(e) => setCategoria(e.target.value)}>
            <option value="Todos">Todas as categorias</option>
            {(categories ?? []).map(cat => (
              <option key={cat.id} value={cat.slug}>{cat.name}</option>
            ))}
          </select>

          <select className="field-control" value={faixaEtaria} onChange={(e) => setFaixaEtaria(e.target.value)}>
            <option value="Todas">Todas as faixas etarias</option>
            {ageRanges.map((ageRange) => (
              <option key={ageRange} value={ageRange}>{ageRange}</option>
            ))}
          </select>
        </div>

        <div className="produtos-toolbar-card__footer">
          <span>{produtosFiltrados.length} {produtosFiltrados.length === 1 ? "produto encontrado" : "produtos encontrados"}</span>

          {(busca || categoria !== "Todos" || faixaEtaria !== "Todas") ? (
            <button
              type="button"
              className="produtos-toolbar-card__reset"
              onClick={() => {
                setBusca("");
                setCategoria("Todos");
                setFaixaEtaria("Todas");
              }}
            >
              Limpar filtros
            </button>
          ) : null}
        </div>
      </section>

      {loading && <LoadingState message="Carregando produtos..." />}
      {error && <ErrorMessage message={error.message} />}

      {!loading && !error && produtosFiltrados.length === 0 && (
        <EmptyState title="Nenhum produto encontrado" message="Tente mudar a categoria, a faixa etaria ou limpar os filtros para explorar outras opcoes." />
      )}

      <div className="grid">
        {(produtosFiltrados ?? []).map(produto => (
          <ProductCard key={produto.id} produto={produto} />
        ))}
      </div>
    </main>
    </>
  );
}
