from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.catalog.service import CatalogService
from datetime import date
from typing import Optional
from app.catalog.schemas import (
    CategoryCreate,
    CategoryOut,
    ProductCreate,
    ProductUpdate,
    ProductStatusUpdate,
    ProductDetailOut
)

from app.core.security import get_current_user


# -------------------------------------------------------------------------
# Rotas do módulo de catálogo
# -------------------
router = APIRouter(
    prefix="/produtos",
    tags=["Catálogo"]
)

product_uploads_dir = Path(settings.UPLOADS_DIR) / "products"
try:
    product_uploads_dir.mkdir(parents=True, exist_ok=True)
except OSError:
    # Filesystem somente leitura (ambiente serverless).
    # Uploads locais ficam indisponiveis; imagens devem vir por URL externa.
    pass


# -------------------------------------------------------------------------
# Lista produtos ativos com filtros opcionais:
# - categoria
# - faixa etária
# - disponibilidade por período
# -------------------------------------------------------------------------
@router.get("/")
async def list_products(
    categoria_id: Optional[int] = None,
    faixa_etaria: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    service = CatalogService(db)

    return await service.get_products(
        categoria_id=categoria_id,
        faixa_etaria=faixa_etaria,
        start_date=start_date,
        end_date=end_date
    )

# -------------------------------------------------------------------------
# Lista todas as categorias ativas do catálogo
# -------------------------------------------------------------------------
@router.get("/categorias")
async def list_categories(
    db: AsyncSession = Depends(get_db)
):
    service = CatalogService(db)
    return await service.get_categories()

# -------------------------------------------------------------------------
# Cadastro de categoria
# Acesso restrito para usuários administradores
# -------------------------------------------------------------------------
@router.post(
    "/admin/categorias",
    response_model=CategoryOut,
    status_code=201
)
async def create_category(
    data: CategoryCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    service = CatalogService(db)

    return await service.create_category(data)


@router.post("/admin/upload-image")
async def upload_product_image(
    request: Request,
    image: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo de imagem válido"
        )

    extension = Path(image.filename or "").suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(
            status_code=400,
            detail="Formato de imagem não suportado"
        )

    file_name = f"{uuid4().hex}{extension}"
    file_path = product_uploads_dir / file_name

    contents = await image.read()
    file_path.write_bytes(contents)

    base_url = str(request.base_url).rstrip("/")
    return {"url": f"{base_url}/uploads/products/{file_name}"}

# -------------------------------------------------------------------------
# Cadastro de produto
# Acesso restrito para usuários administradores
# -------------------------------------------------------------------------
@router.post(
    "/admin",
    response_model=ProductDetailOut,
    status_code=201
)
async def create_product(
    data: ProductCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    service = CatalogService(db)

    return await service.create_product(data)


@router.get(
    "/admin",
    response_model=list[ProductDetailOut]
)
async def list_admin_products(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    service = CatalogService(db)
    return await service.get_admin_products()


@router.get("/admin/resumo")
async def get_admin_products_summary(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    service = CatalogService(db)
    return await service.get_admin_products_summary()

# -------------------------------------------------------------------------
# Atualização de produto
# Permite atualização parcial dos dados do produto
# Acesso restrito para administradores
# -------------------------------------------------------------------------
@router.put(
    "/admin/{product_id}",
    response_model=ProductDetailOut
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    service = CatalogService(db)

    return await service.update_product(
        product_id,
        data
    )

# -------------------------------------------------------------------------
# Ativa ou desativa um produto no catálogo
# Produtos inativos não aparecem na listagem pública
# Acesso restrito para administradores
# -------------------------------------------------------------------------
@router.patch(
    "/admin/{product_id}/status",
    response_model=ProductDetailOut
)
async def update_product_status(
    product_id: int,
    data: ProductStatusUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    service = CatalogService(db)

    return await service.update_product_status(
        product_id,
        data.ativo
    )


@router.delete(
    "/admin/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_product(
    product_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem realizar esta ação"
        )

    service = CatalogService(db)
    await service.delete_product(product_id)

# -------------------------------------------------------------------------
# Retorna os detalhes completos de um produto pelo ID
# -------------------------------------------------------------------------
@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = CatalogService(db)
    return await service.get_product_by_id(product_id)
