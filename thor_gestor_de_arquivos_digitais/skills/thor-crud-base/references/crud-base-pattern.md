# Padrão CRUD Base

Esta referência é autocontida. Use-a mesmo quando não houver código CRUD existente disponível.

## Estrutura de Arquivos Sugerida

Para um projeto Next.js App Router:

```text
backend/
  app/
    api/
      v1/
        products.py
        router.py
    models/
      product.py
    schemas/
      product.py
    services/
      product_service.py
    repositories/
      product_repo.py
    tests/
      test_products.py
  alembic/
    versions/
      <timestamp>_products.py

frontend/
  app/
    (app)/
      products/
        page.tsx
        new/
          page.tsx
        [id]/
          edit/
            page.tsx
  features/
    products/
      product-form.tsx
      products-table.tsx
      product-edit-page.tsx
  lib/
    api/
      products.ts
  types/
    products.ts
```

Adapte os nomes ao idioma do projeto. Em rotas em português, `/produtos/novo` ou `/produtos/nova` funciona bem quando combina com o gênero da entidade e com o estilo de rotas existente. Para edição, use uma rota dedicada como `/produtos/{id}/editar`.

## Contrato do Backend

Use uma API backend que o frontend consiga consumir sem adivinhação:

```text
GET    /api/v1/products?limit=20&offset=0&q=abc&status=ACTIVE
GET    /api/v1/products/{id}
POST   /api/v1/products
PUT    /api/v1/products/{id}
DELETE /api/v1/products/{id}
```

Resposta da listagem:

```json
{
  "items": [],
  "total": 0
}
```

Regras:

- Valide campos obrigatórios e enums no backend.
- Aplique constraints únicas no banco de dados.
- Aplique filtros na consulta do banco de dados.
- Limite `limit` a um máximo seguro, como `100`.
- Retorne uma ordenação estável.
- Retorne `404` para IDs ausentes e `409` para conflitos.

## Exemplo de Modelo Backend

Exemplo de modelo no estilo SQLAlchemy:

```py
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProductCategory(StrEnum):
    BOOK = "BOOK"
    MEDIA = "MEDIA"
    EQUIPMENT = "EQUIPMENT"


class ProductStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[ProductCategory] = mapped_column(Enum(ProductCategory), nullable=False)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

Checklist de migração:

- criar tabela
- adicionar colunas obrigatórias e anuláveis corretamente
- adicionar constraint única para identificadores de negócio
- adicionar índices para campos usados em busca/filtro/ordenação
- adicionar chaves estrangeiras para relacionamentos
- definir o comportamento de criação/remoção de enums conforme o banco de dados

## Exemplo de Schemas Backend

Exemplo de schemas no estilo Pydantic:

```py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.product import ProductCategory, ProductStatus


class ProductBase(BaseModel):
    code: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category: ProductCategory
    status: ProductStatus = ProductStatus.ACTIVE


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=100)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category: ProductCategory | None = None
    status: ProductStatus | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductRead]
    total: int
```

Se a stack usar outro framework, mantenha os mesmos conceitos: payload de criação, payload de atualização, DTO de leitura, DTO de página, validação de enum e limites de campo.

## Exemplo de Repositório Backend

Mantenha a construção de consultas em um repositório/helper de query para que os filtros continuem testáveis:

```py
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.product import Product, ProductCategory, ProductStatus


class ProductFilters:
    def __init__(
        self,
        q: str | None = None,
        code: str | None = None,
        name: str | None = None,
        category: ProductCategory | None = None,
        status: ProductStatus | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> None:
        self.q = q
        self.code = code
        self.name = name
        self.category = category
        self.status = status
        self.created_from = created_from
        self.created_to = created_to


def apply_product_filters(query: Select[tuple[Product]], filters: ProductFilters) -> Select[tuple[Product]]:
    if filters.q:
        pattern = f"%{filters.q.strip()}%"
        query = query.where(or_(Product.code.ilike(pattern), Product.name.ilike(pattern)))
    if filters.code:
        query = query.where(Product.code.ilike(f"%{filters.code.strip()}%"))
    if filters.name:
        query = query.where(Product.name.ilike(f"%{filters.name.strip()}%"))
    if filters.category:
        query = query.where(Product.category == filters.category)
    if filters.status:
        query = query.where(Product.status == filters.status)
    if filters.created_from:
        query = query.where(Product.created_at >= filters.created_from)
    if filters.created_to:
        query = query.where(Product.created_at <= filters.created_to)
    return query


def list_products(db: Session, filters: ProductFilters, limit: int, offset: int) -> tuple[list[Product], int]:
    base_query = apply_product_filters(select(Product), filters)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(
        base_query.order_by(Product.created_at.desc(), Product.id.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_product_by_code(db: Session, code: str) -> Product | None:
    return db.scalar(select(Product).where(Product.code == code))
```

## Exemplo de Serviço Backend

Mantenha regras de negócio nos serviços:

```py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repo import get_product, get_product_by_code, list_products, ProductFilters
from app.schemas.product import ProductCreate, ProductUpdate


def list_products_page(db: Session, filters: ProductFilters, limit: int, offset: int) -> tuple[list[Product], int]:
    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    return list_products(db, filters, safe_limit, safe_offset)


def create_product(db: Session, payload: ProductCreate) -> Product:
    if get_product_by_code(db, payload.code):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código do produto já existe.")

    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    values = payload.model_dump(exclude_unset=True)
    next_code = values.get("code")
    if next_code and next_code != product.code and get_product_by_code(db, next_code):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código do produto já existe.")

    for field, value in values.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    db.delete(product)
    db.commit()
```

Se as regras de negócio exigirem auditabilidade, prefira exclusão lógica ou transição de status em vez de exclusão física.

## Exemplo de Router Backend

Exemplo de router FastAPI:

```py
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import ProductCategory, ProductStatus
from app.repositories.product_repo import ProductFilters
from app.schemas.product import ProductCreate, ProductPage, ProductRead, ProductUpdate
from app.services.product_service import create_product, delete_product, list_products_page, update_product
from app.repositories.product_repo import get_product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPage)
def list_products_endpoint(
    q: str | None = None,
    code: str | None = None,
    name: str | None = None,
    category: ProductCategory | None = None,
    status: ProductStatus | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ProductPage:
    filters = ProductFilters(
        q=q,
        code=code,
        name=name,
        category=category,
        status=status,
        created_from=created_from,
        created_to=created_to,
    )
    items, total = list_products_page(db, filters, limit, offset)
    return ProductPage(items=items, total=total)


@router.get("/{product_id}", response_model=ProductRead)
def get_product_endpoint(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    product = get_product(db, product_id)
    if not product:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return product


@router.post("", response_model=ProductRead, status_code=201)
def create_product_endpoint(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    return create_product(db, payload)


@router.put("/{product_id}", response_model=ProductRead)
def update_product_endpoint(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> ProductRead:
    return update_product(db, product_id, payload)


@router.delete("/{product_id}", status_code=204)
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)) -> None:
    delete_product(db, product_id)
```

Registre o router no arquivo central de rotas da API:

```py
api_router.include_router(products.router)
```

## Checklist de Testes Backend

Adicione testes no nível da API ou do serviço para:

- criação com sucesso usando campos obrigatórios válidos
- criação rejeita campos obrigatórios ausentes
- criação rejeita identificadores únicos duplicados
- listagem retorna `{ items, total }`
- busca simples por `q` encontra os campos esperados
- filtros avançados são aplicados de forma independente e em conjunto
- paginação respeita `limit` e `offset`
- tamanho máximo de página é aplicado
- obter/atualizar/excluir retornam `404` para IDs ausentes
- atualização rejeita conflitos de unicidade
- exclusão remove, exclui logicamente ou desativa conforme a regra

Formato de exemplo para teste de API:

```py
def test_list_products_paginates(client):
    response = client.get("/api/v1/products?limit=20&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)
```

## Tipos e Formato da API

Use um formato de listagem paginada:

```ts
export type Product = {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  category: "BOOK" | "MEDIA" | "EQUIPMENT";
  status: "ACTIVE" | "INACTIVE";
  createdAt?: string;
  updatedAt?: string;
};

export type ProductFilters = {
  q?: string;
  code?: string;
  name?: string;
  category?: Product["category"] | "";
  status?: Product["status"] | "";
  createdFrom?: string;
  createdTo?: string;
};

export type Page<T> = {
  items: T[];
  total: number;
};

export type ListProductsParams = {
  limit: number;
  offset: number;
  filters: ProductFilters;
};
```

Funções de API podem encapsular qualquer cliente HTTP:

```ts
export async function listProductsPage(params: ListProductsParams): Promise<Page<Product>> {
  const search = new URLSearchParams();
  search.set("limit", String(params.limit));
  search.set("offset", String(params.offset));

  Object.entries(params.filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });

  const response = await fetch(`/api/products?${search.toString()}`);
  if (!response.ok) {
    throw new Error("Falha ao carregar produtos.");
  }
  return response.json();
}

export async function createProduct(payload: ProductPayload): Promise<Product> {
  const response = await fetch("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Falha ao criar produto.");
  }
  return response.json();
}

export async function getProduct(id: number): Promise<Product> {
  const response = await fetch(`/api/products/${id}`);
  if (!response.ok) {
    throw new Error("Falha ao carregar produto.");
  }
  return response.json();
}

export async function updateProduct(id: number, payload: ProductPayload): Promise<Product> {
  const response = await fetch(`/api/products/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Falha ao atualizar produto.");
  }
  return response.json();
}

export async function deleteProduct(id: number): Promise<void> {
  const response = await fetch(`/api/products/${id}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error("Falha ao excluir produto.");
  }
}
```

## Exemplo de Página de Listagem

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductsTable } from "@/features/products/products-table";
import { listProductsPage, type ProductFilters } from "@/lib/api/products";

export default function ProductsPage() {
  const [filters, setFilters] = useState<ProductFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  const query = useQuery({
    queryKey: ["products", filters, pageIndex, pageSize],
    queryFn: () =>
      listProductsPage({
        limit: pageSize,
        offset: pageIndex * pageSize,
        filters,
      }),
  });

  const products = query.data?.items ?? [];
  const total = query.data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Produtos</h1>
          <p className="text-sm text-muted-foreground">Cadastre, busque e gerencie produtos.</p>
        </div>
        <Button asChild>
          <Link href="/products/new">
            <Plus className="h-4 w-4" />
            Novo produto
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Catálogo</CardTitle>
          <CardDescription>
            {query.isLoading ? "Carregando registros..." : `${total} registros encontrados`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : (
            <ProductsTable
              data={products}
              filters={filters}
              onSearch={(nextFilters) => {
                setFilters(nextFilters);
                setPageIndex(0);
              }}
              pageIndex={pageIndex}
              pageSize={pageSize}
              total={total}
              isLoading={query.isFetching}
              onPageChange={setPageIndex}
              onPageSizeChange={(nextPageSize) => {
                setPageSize(nextPageSize);
                setPageIndex(0);
              }}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

## Exemplo de Página de Criação

```tsx
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductForm } from "@/features/products/product-form";

export default function NewProductPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Novo produto</h1>
          <p className="text-sm text-muted-foreground">Preencha os principais metadados do produto.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/products">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Criar</CardTitle>
          <CardDescription>Campos obrigatórios são marcados com asterisco.</CardDescription>
        </CardHeader>
        <CardContent>
          <ProductForm onSaved={() => router.push("/products")} />
        </CardContent>
      </Card>
    </div>
  );
}
```

## Exemplo de Página de Edição

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductForm } from "@/features/products/product-form";
import { getProduct } from "@/lib/api/products";

type Props = {
  productId: number;
};

export function ProductEditPage({ productId }: Props) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["products", productId],
    queryFn: () => getProduct(productId),
    enabled: Number.isFinite(productId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar produto</h1>
          <p className="text-sm text-muted-foreground">Atualize os principais metadados do produto.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/products">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Edição</CardTitle>
          <CardDescription>
            {query.data ? `Produto ${query.data.code}` : "Carregando dados do produto."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando produto...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : query.data ? (
            <ProductForm product={query.data} onSaved={() => router.push("/products")} />
          ) : (
            <p className="text-sm text-muted-foreground">Produto não encontrado.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

Arquivo de rota para Next.js App Router:

```tsx
import { ProductEditPage } from "@/features/products/product-edit-page";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  return <ProductEditPage productId={Number(id)} />;
}
```

## Exemplo de Tabela

```tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { Edit, Eye, Filter, Search, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { deleteProduct, type ProductFilters } from "@/lib/api/products";
import type { Product } from "@/types/products";

type Props = {
  data: Product[];
  filters: ProductFilters;
  onSearch: (filters: ProductFilters) => void;
  pageIndex: number;
  pageSize: number;
  total: number;
  isLoading: boolean;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
};

export function ProductsTable({
  data,
  filters,
  onSearch,
  pageIndex,
  pageSize,
  total,
  isLoading,
  onPageChange,
  onPageSizeChange,
}: Props) {
  const queryClient = useQueryClient();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftFilters, setDraftFilters] = useState<ProductFilters>(filters);
  const [selected, setSelected] = useState<Product | null>(null);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  useEffect(() => {
    setDraftFilters(filters);
  }, [filters]);

  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      setSelected(null);
    },
  });

  const columns = useMemo<ColumnDef<Product>[]>(
    () => [
      {
        accessorKey: "code",
        header: "Código",
        cell: ({ row }) => (
          <button
            className="font-medium text-primary hover:underline"
            type="button"
            onClick={() => setSelected(row.original)}
          >
            {row.original.code}
          </button>
        ),
      },
      { accessorKey: "name", header: "Nome" },
      { accessorKey: "category", header: "Categoria" },
      { accessorKey: "status", header: "Status" },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <div className="flex justify-end gap-1">
            <Button aria-label="Visualizar" size="icon" type="button" variant="ghost" onClick={() => setSelected(row.original)}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button asChild aria-label="Editar" size="icon" variant="ghost">
              <Link href={`/products/${row.original.id}/edit`}>
                <Edit className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        ),
      },
    ],
    [],
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar"
            value={draftFilters.q ?? ""}
            onChange={(event) => setDraftFilters({ ...draftFilters, q: event.target.value })}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onSearch(draftFilters);
              }
            }}
          />
        </div>
        <Button type="button" onClick={() => onSearch(draftFilters)}>
          <Search className="h-4 w-4" />
          Buscar
        </Button>
        <Button type="button" variant="outline" onClick={() => setShowAdvanced((value) => !value)}>
          <Filter className="h-4 w-4" />
          Filtros avançados
        </Button>
      </div>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={data.length}
        total={total}
        isLoading={isLoading}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          <FilterField label="Código">
            <Input value={draftFilters.code ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, code: event.target.value })} />
          </FilterField>
          <FilterField label="Nome">
            <Input value={draftFilters.name ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, name: event.target.value })} />
          </FilterField>
          <SelectFilter label="Categoria" value={draftFilters.category ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, category: value as ProductFilters["category"] })}>
            <option value="">Todos</option>
            <option value="BOOK">Livro</option>
            <option value="MEDIA">Mídia</option>
            <option value="EQUIPMENT">Equipamento</option>
          </SelectFilter>
          <SelectFilter label="Status" value={draftFilters.status ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, status: value as ProductFilters["status"] })}>
            <option value="">Todos</option>
            <option value="ACTIVE">Ativo</option>
            <option value="INACTIVE">Inativo</option>
          </SelectFilter>
          <DateRangeFilter
            label="Criado em"
            from={draftFilters.createdFrom}
            to={draftFilters.createdTo}
            onChange={(from, to) => setDraftFilters({ ...draftFilters, createdFrom: from, createdTo: to })}
          />
          <div className="flex items-end gap-2">
            <Button type="button" onClick={() => onSearch(draftFilters)}>
              <Search className="h-4 w-4" />
              Buscar
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setDraftFilters({});
                onSearch({});
              }}
            >
              Limpar
            </Button>
          </div>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                  Nenhum registro encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={data.length}
        total={total}
        isLoading={isLoading}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />

      {selected ? (
        <div className="rounded-md border p-4">
          <div className="grid gap-3 md:grid-cols-2">
            <DetailLine label="Código" value={selected.code} />
            <DetailLine label="Nome" value={selected.name} />
            <DetailLine label="Categoria" value={selected.category} />
            <DetailLine label="Status" value={selected.status} />
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <Button asChild variant="outline">
              <Link href={`/products/${selected.id}/edit`}>
                <Edit className="h-4 w-4" />
                Editar
              </Link>
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (window.confirm("Excluir este registro?")) {
                  deleteMutation.mutate(selected.id);
                }
              }}
            >
              <Trash2 className="h-4 w-4" />
              {deleteMutation.isPending ? "Excluindo..." : "Excluir"}
            </Button>
          </div>
        </div>
      ) : null}

    </div>
  );
}
```

## Helpers de Paginação

```tsx
function PaginationControls({
  currentPage,
  totalPages,
  pageSize,
  displayedCount,
  total,
  isLoading,
  onPageChange,
  onPageSizeChange,
}: {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  displayedCount: number;
  total: number;
  isLoading: boolean;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}) {
  const pages = getPaginationItems(currentPage, totalPages);

  return (
    <div className="flex flex-col gap-3 rounded-md border px-3 py-2">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <p className="text-sm text-muted-foreground">
          {displayedCount} registros de {total} | página {currentPage} de {totalPages}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>
            Primeira
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>
            Anterior
          </Button>
          {pages.map((page, index) =>
            page === "ellipsis" ? (
              <span key={`ellipsis-${index}`} className="flex h-9 min-w-9 items-center justify-center px-2 text-sm text-muted-foreground">
                ...
              </span>
            ) : (
              <Button
                key={page}
                type="button"
                variant={page === currentPage ? "default" : "outline"}
                size="sm"
                className="min-w-9 px-2"
                disabled={isLoading || page === currentPage}
                onClick={() => onPageChange(page - 1)}
              >
                {page}
              </Button>
            ),
          )}
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>
            Próxima
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>
            Última
          </Button>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Label htmlFor="page-size" className="text-sm text-muted-foreground">
          Registros por página:
        </Label>
        <select
          id="page-size"
          className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
}

function getPaginationItems(currentPage: number, totalPages: number) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
  const sortedPages = Array.from(pages)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right);

  return sortedPages.flatMap((page, index) => {
    const previousPage = sortedPages[index - 1];
    return previousPage && page - previousPage > 1 ? ["ellipsis" as const, page] : [page];
  });
}
```

## Helpers de Filtros

```tsx
function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function SelectFilter({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return (
    <FilterField label={label}>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {children}
      </select>
    </FilterField>
  );
}

function DateRangeFilter({
  label,
  from,
  to,
  onChange,
}: {
  label: string;
  from?: string;
  to?: string;
  onChange: (from: string, to: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="grid gap-2 sm:grid-cols-2">
        <Input
          aria-label={`${label} de`}
          type="date"
          value={from?.slice(0, 10) ?? ""}
          onChange={(event) => onChange(startOfDay(event.target.value), to ?? "")}
        />
        <Input
          aria-label={`${label} até`}
          type="date"
          value={to?.slice(0, 10) ?? ""}
          onChange={(event) => onChange(from ?? "", endOfDay(event.target.value))}
        />
      </div>
    </div>
  );
}

function startOfDay(value: string) {
  return value ? `${value}T00:00:00` : "";
}

function endOfDay(value: string) {
  return value ? `${value}T23:59:59` : "";
}

function DetailLine({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <div className="mt-1 text-sm">{value}</div>
    </div>
  );
}
```

## Exemplo de Formulário

```tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createProduct, listCategories, updateProduct } from "@/lib/api/products";
import type { Product } from "@/types/products";

const schema = z
  .object({
    code: z.string().min(2).max(100),
    name: z.string().min(2).max(255),
    description: z.string().max(2000).optional(),
    category: z.enum(["BOOK", "MEDIA", "EQUIPMENT"]),
    status: z.enum(["ACTIVE", "INACTIVE"]),
    ownerId: z.string().optional(),
    hasWarranty: z.boolean(),
    warrantyUntil: z.string().optional(),
  })
  .superRefine((values, ctx) => {
    if (values.hasWarranty && !values.warrantyUntil) {
      ctx.addIssue({
        code: "custom",
        path: ["warrantyUntil"],
        message: "A data da garantia é obrigatória quando a garantia está habilitada.",
      });
    }
  });

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  code: "",
  name: "",
  description: "",
  category: "BOOK",
  status: "ACTIVE",
  ownerId: "",
  hasWarranty: false,
  warrantyUntil: "",
};

export function ProductForm({
  product,
  onSaved,
}: {
  product?: Product;
  onSaved?: () => void;
}) {
  const queryClient = useQueryClient();
  const isEditing = Boolean(product);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });
  const hasWarranty = form.watch("hasWarranty");

  const categories = useQuery({
    queryKey: ["product-categories"],
    queryFn: listCategories,
    enabled: true,
  });

  useEffect(() => {
    if (!product) {
      form.reset(defaultValues);
      return;
    }

    form.reset({
      ...defaultValues,
      code: product.code,
      name: product.name,
      description: product.description ?? "",
      category: product.category,
      status: product.status,
    });
  }, [form, product]);

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        code: values.code.trim(),
        name: values.name.trim(),
        description: values.description?.trim() || null,
        category: values.category,
        status: values.status,
        ownerId: toOptionalNumber(values.ownerId),
        warrantyUntil: values.hasWarranty ? values.warrantyUntil || null : null,
      };

      return product ? updateProduct(product.id, payload) : createProduct(payload);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["products"] }),
        queryClient.invalidateQueries({ queryKey: ["product-categories"] }),
      ]);
      if (!isEditing) {
        form.reset(defaultValues);
      }
      onSaved?.();
    },
  });

  return (
    <form className="space-y-5" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Código" error={form.formState.errors.code?.message} required>
          <Input {...form.register("code")} required />
        </Field>
        <Field label="Nome" error={form.formState.errors.name?.message} required>
          <Input {...form.register("name")} required />
        </Field>
      </div>

      <Field label="Descrição" error={form.formState.errors.description?.message}>
        <textarea
          className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("description")}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Categoria" error={form.formState.errors.category?.message} {...form.register("category")} required>
          {(categories.data ?? ["BOOK", "MEDIA", "EQUIPMENT"]).map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </SelectField>
        <SelectField label="Status" error={form.formState.errors.status?.message} {...form.register("status")} required>
          <option value="ACTIVE">Ativo</option>
          <option value="INACTIVE">Inativo</option>
        </SelectField>
        <Field label="ID do responsável" error={form.formState.errors.ownerId?.message}>
          <Input type="number" min={1} {...form.register("ownerId")} />
        </Field>
      </div>

      <section className="space-y-4 rounded-md border p-4">
        <label className="flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" {...form.register("hasWarranty")} />
          Tem garantia
        </label>
        {hasWarranty ? (
          <Field label="Garantia até" error={form.formState.errors.warrantyUntil?.message} required>
            <Input type="date" {...form.register("warrantyUntil")} required />
          </Field>
        ) : null}
      </section>

      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Salvando..." : isEditing ? "Salvar alterações" : "Salvar"}
      </Button>
    </form>
  );
}

function Field({
  label,
  error,
  children,
  required,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
  required?: boolean;
}) {
  return (
    <div className="space-y-2">
      <RequiredLabel required={required}>{label}</RequiredLabel>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function RequiredLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <Label>
      {children}
      {required ? (
        <span className="ml-1 text-destructive" aria-label="obrigatório">
          *
        </span>
      ) : null}
    </Label>
  );
}

function SelectField({
  label,
  error,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  error?: string;
}) {
  return (
    <div className="space-y-2">
      <RequiredLabel required={props.required}>{label}</RequiredLabel>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        {...props}
      >
        {children}
      </select>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function toOptionalNumber(value?: string) {
  return value ? Number(value) : null;
}
```

## Checklist de Carregamento Sob Demanda

- Mantenha consultas de listagem paginadas.
- Inclua filtros e estado de paginação na query key.
- Use `enabled` para consultas de detalhes que exigem um registro selecionado.
- Use `enabled` para consultas de edição que dependem do ID da rota.
- Use `enabled` para consultas de listas de opções que devem aguardar um modo ou seção visível.
- Use skeletons ou texto de carregamento conciso para a carga inicial.
- Use `isFetching` para desabilitar a paginação enquanto mantém os dados antigos.

Exemplo de consulta de detalhes:

```tsx
const details = useQuery({
  queryKey: ["products", selectedId],
  queryFn: () => getProduct(selectedId ?? 0),
  enabled: Boolean(selectedId),
});
```

Exemplo de consulta de edição:

```tsx
const product = useQuery({
  queryKey: ["products", productId],
  queryFn: () => getProduct(productId),
  enabled: Number.isFinite(productId),
});
```

## Checklist de Verificação

- A ação de criar abre uma página completa, não um popup.
- A página de criação tem um botão Voltar.
- Criação bem-sucedida retorna para a listagem ou para o destino solicitado.
- A ação de editar abre uma página completa, não um popup.
- A página de edição carrega a entidade por ID da rota.
- A página de edição tem um botão Voltar.
- Edição bem-sucedida retorna para a listagem ou para o destino solicitado.
- Busca simples submete com Enter e clique no botão.
- Buscas simples e avançadas redefinem para a página 1.
- Limpar filtros redefine os filtros em rascunho e os filtros submetidos.
- A paginação é server-side e tem estados desabilitados durante a busca.
- Mudanças no tamanho da página redefinem para a página 1.
- Campos obrigatórios existem tanto no schema quanto na UI.
- Campos obrigatórios condicionais são aplicados no schema e na UI.
- Mutações invalidam consultas de listagem.
- Exclusão pede confirmação.
- Typecheck/build/testes rodam quando disponíveis.
