# CRUD Base Pattern

This reference is self-contained. Use it even when no existing CRUD code is available.

## Suggested File Structure

For a Next.js App Router project:

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
  features/
    products/
      product-form.tsx
      products-table.tsx
  lib/
    api/
      products.ts
  types/
    products.ts
```

Adapt names to the project language. In Portuguese routes, `/produtos/novo` or `/produtos/nova` is fine when it matches the entity gender and existing route style.

## Backend Contract

Use a backend API that the frontend can consume without guessing:

```text
GET    /api/v1/products?limit=20&offset=0&q=abc&status=ACTIVE
GET    /api/v1/products/{id}
POST   /api/v1/products
PUT    /api/v1/products/{id}
DELETE /api/v1/products/{id}
```

List response:

```json
{
  "items": [],
  "total": 0
}
```

Rules:

- Validate required fields and enums on the backend.
- Enforce unique constraints in the database.
- Apply filters in the database query.
- Cap `limit` to a safe maximum such as `100`.
- Return stable ordering.
- Return `404` for missing IDs and `409` for conflicts.

## Backend Model Example

Example SQLAlchemy-style model:

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

Migration checklist:

- create table
- add required and nullable columns correctly
- add unique constraint for business identifiers
- add indexes for fields used in search/filter/order
- add foreign keys for relationships
- define enum creation/drop behavior according to the database

## Backend Schemas Example

Example Pydantic-style schemas:

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

If the stack uses another framework, keep the same concepts: create payload, update payload, read DTO, page DTO, enum validation, and field limits.

## Backend Repository Example

Keep query construction in a repository/query helper so filters stay testable:

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

## Backend Service Example

Keep business rules in services:

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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product code already exists.")

    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    values = payload.model_dump(exclude_unset=True)
    next_code = values.get("code")
    if next_code and next_code != product.code and get_product_by_code(db, next_code):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product code already exists.")

    for field, value in values.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    db.delete(product)
    db.commit()
```

If business rules require auditability, prefer soft delete or status transition instead of physical delete.

## Backend Router Example

Example FastAPI router:

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

        raise HTTPException(status_code=404, detail="Product not found.")
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

Register the router in the API's central router file:

```py
api_router.include_router(products.router)
```

## Backend Tests Checklist

Add tests at the API or service level for:

- create succeeds with valid required fields
- create rejects missing required fields
- create rejects duplicate unique identifiers
- list returns `{ items, total }`
- simple `q` search matches expected fields
- advanced filters apply independently and together
- pagination respects `limit` and `offset`
- max page size is enforced
- get/update/delete return `404` for missing IDs
- update rejects uniqueness conflicts
- delete removes, soft-deletes, or deactivates according to the rule

Example API test shape:

```py
def test_list_products_paginates(client):
    response = client.get("/api/v1/products?limit=20&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)
```

## Types And API Shape

Use a paginated list shape:

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

API functions can wrap any HTTP client:

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
    throw new Error("Failed to load products.");
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
    throw new Error("Failed to create product.");
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
    throw new Error("Failed to update product.");
  }
  return response.json();
}

export async function deleteProduct(id: number): Promise<void> {
  const response = await fetch(`/api/products/${id}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error("Failed to delete product.");
  }
}
```

## List Page Example

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
          <h1 className="text-2xl font-semibold tracking-normal">Products</h1>
          <p className="text-sm text-muted-foreground">Register, search, and manage products.</p>
        </div>
        <Button asChild>
          <Link href="/products/new">
            <Plus className="h-4 w-4" />
            New product
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Catalog</CardTitle>
          <CardDescription>
            {query.isLoading ? "Loading records..." : `${total} records found`}
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

## Create Page Example

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
          <h1 className="text-2xl font-semibold tracking-normal">New product</h1>
          <p className="text-sm text-muted-foreground">Fill in the main product metadata.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/products">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create</CardTitle>
          <CardDescription>Required fields are marked with an asterisk.</CardDescription>
        </CardHeader>
        <CardContent>
          <ProductForm onSaved={() => router.push("/products")} />
        </CardContent>
      </Card>
    </div>
  );
}
```

## Table Example

```tsx
"use client";

import { useEffect, useMemo, useState } from "react";
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
  const [editing, setEditing] = useState<Product | null>(null);
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
        header: "Code",
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
      { accessorKey: "name", header: "Name" },
      { accessorKey: "category", header: "Category" },
      { accessorKey: "status", header: "Status" },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <div className="flex justify-end gap-1">
            <Button aria-label="View" size="icon" type="button" variant="ghost" onClick={() => setSelected(row.original)}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button aria-label="Edit" size="icon" type="button" variant="ghost" onClick={() => setEditing(row.original)}>
              <Edit className="h-4 w-4" />
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
            placeholder="Search"
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
          Search
        </Button>
        <Button type="button" variant="outline" onClick={() => setShowAdvanced((value) => !value)}>
          <Filter className="h-4 w-4" />
          Advanced filters
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
          <FilterField label="Code">
            <Input value={draftFilters.code ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, code: event.target.value })} />
          </FilterField>
          <FilterField label="Name">
            <Input value={draftFilters.name ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, name: event.target.value })} />
          </FilterField>
          <SelectFilter label="Category" value={draftFilters.category ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, category: value as ProductFilters["category"] })}>
            <option value="">All</option>
            <option value="BOOK">Book</option>
            <option value="MEDIA">Media</option>
            <option value="EQUIPMENT">Equipment</option>
          </SelectFilter>
          <SelectFilter label="Status" value={draftFilters.status ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, status: value as ProductFilters["status"] })}>
            <option value="">All</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </SelectFilter>
          <DateRangeFilter
            label="Created"
            from={draftFilters.createdFrom}
            to={draftFilters.createdTo}
            onChange={(from, to) => setDraftFilters({ ...draftFilters, createdFrom: from, createdTo: to })}
          />
          <div className="flex items-end gap-2">
            <Button type="button" onClick={() => onSearch(draftFilters)}>
              <Search className="h-4 w-4" />
              Search
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setDraftFilters({});
                onSearch({});
              }}
            >
              Clear
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
                  No records found.
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
            <DetailLine label="Code" value={selected.code} />
            <DetailLine label="Name" value={selected.name} />
            <DetailLine label="Category" value={selected.category} />
            <DetailLine label="Status" value={selected.status} />
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setEditing(selected)}>
              <Edit className="h-4 w-4" />
              Edit
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (window.confirm("Delete this record?")) {
                  deleteMutation.mutate(selected.id);
                }
              }}
            >
              <Trash2 className="h-4 w-4" />
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </div>
        </div>
      ) : null}

      {editing ? (
        <div className="rounded-md border p-4">
          {/* Replace with a route or dialog when the project has that pattern. */}
          {/* <ProductForm product={editing} onSaved={() => setEditing(null)} /> */}
        </div>
      ) : null}
    </div>
  );
}
```

## Pagination Helpers

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
          {displayedCount} records of {total} | page {currentPage} of {totalPages}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>
            First
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>
            Previous
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
            Next
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>
            Last
          </Button>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Label htmlFor="page-size" className="text-sm text-muted-foreground">
          Records per page:
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

## Filter Helpers

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
          aria-label={`${label} from`}
          type="date"
          value={from?.slice(0, 10) ?? ""}
          onChange={(event) => onChange(startOfDay(event.target.value), to ?? "")}
        />
        <Input
          aria-label={`${label} to`}
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

## Form Example

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
        message: "Warranty date is required when warranty is enabled.",
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
        <Field label="Code" error={form.formState.errors.code?.message} required>
          <Input {...form.register("code")} required />
        </Field>
        <Field label="Name" error={form.formState.errors.name?.message} required>
          <Input {...form.register("name")} required />
        </Field>
      </div>

      <Field label="Description" error={form.formState.errors.description?.message}>
        <textarea
          className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("description")}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Category" error={form.formState.errors.category?.message} {...form.register("category")} required>
          {(categories.data ?? ["BOOK", "MEDIA", "EQUIPMENT"]).map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </SelectField>
        <SelectField label="Status" error={form.formState.errors.status?.message} {...form.register("status")} required>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </SelectField>
        <Field label="Owner ID" error={form.formState.errors.ownerId?.message}>
          <Input type="number" min={1} {...form.register("ownerId")} />
        </Field>
      </div>

      <section className="space-y-4 rounded-md border p-4">
        <label className="flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" {...form.register("hasWarranty")} />
          Has warranty
        </label>
        {hasWarranty ? (
          <Field label="Warranty until" error={form.formState.errors.warrantyUntil?.message} required>
            <Input type="date" {...form.register("warrantyUntil")} required />
          </Field>
        ) : null}
      </section>

      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Saving..." : isEditing ? "Save changes" : "Save"}
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
        <span className="ml-1 text-destructive" aria-label="required">
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

## Lazy Loading Checklist

- Keep list queries paginated.
- Include filters and pagination state in the query key.
- Use `enabled` for detail queries that require a selected record.
- Use `enabled` for option-list queries that should wait for a mode or visible section.
- Use skeletons or concise loading text for initial load.
- Use `isFetching` to disable pagination while retaining old data.

Example detail query:

```tsx
const details = useQuery({
  queryKey: ["products", selectedId],
  queryFn: () => getProduct(selectedId ?? 0),
  enabled: Boolean(selectedId),
});
```

## Verification Checklist

- Create action opens a full page, not a popup.
- Create page has a Back button.
- Successful create returns to the list or the requested destination.
- Simple search submits on Enter and button click.
- Simple and advanced searches reset to page 1.
- Clear filters resets draft filters and submitted filters.
- Pagination is server-side and has disabled states while fetching.
- Page-size changes reset to page 1.
- Required fields exist in both schema and UI.
- Conditional required fields are enforced in schema and UI.
- Mutations invalidate list queries.
- Delete asks for confirmation.
- Typecheck/build/tests run when available.
