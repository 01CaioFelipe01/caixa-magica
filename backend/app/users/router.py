from fastapi import APIRouter, status, Depends, Query, HTTPException, Request
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from app.core.security import get_current_user 

from app.database import get_db  
from app.users.schemas import UserCreate, AdminUserPaginatedResponse, UserOut, LoginRequest, TokenOut, AddressCreate, AddressOut, OrderHistoryPaginatedResponse, AdminOrderPaginatedResponse
from app.users.service import UserService

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

auth_router = APIRouter(prefix="/auth", tags=["Usuários"])
users_router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@auth_router.post(
    "/register", 
    response_model=UserOut, 
    status_code=status.HTTP_201_CREATED
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Instancia o serviço passando a sessão do banco de dados
    user_service = UserService(db)
    
    # Executa a lógica de cadastro e guarda o usuário retornado
    new_user = await user_service.register(data)
    
    return new_user

@auth_router.post(
    "/admin/register-admin", 
    response_model=UserOut, 
    status_code=status.HTTP_201_CREATED
)
async def register_admin_master(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    
    new_user = await user_service.register(data)
    
    new_user.role = "admin"
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@auth_router.post(
    "/login", 
    response_model=TokenOut, 
    status_code=status.HTTP_200_OK
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest, 
    db: AsyncSession = Depends(get_db)):  # <- Mudou aqui
    user_service = UserService(db)
    
    token_response = await user_service.authenticate(data)
    
    return token_response

@auth_router.post(
    "/login-swagger", 
    response_model=TokenOut, 
    status_code=status.HTTP_200_OK,
    include_in_schema=True 
)
@limiter.limit("5/minute")
async def login_swagger(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    
    data = LoginRequest(
        email=form_data.username, 
        password=form_data.password
    )
    
    token_response = await user_service.authenticate(data)
    
    return token_response

@users_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserOut)
async def get_me(current_user = Depends(get_current_user)):
    return current_user


@users_router.get(
    "/me/pedidos", 
    status_code=status.HTTP_200_OK, 
    response_model=OrderHistoryPaginatedResponse
)
async def get_my_orders(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, description="Itens por página"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    
    result = await user_service.get_user_orders(
        user_id=current_user.id, # Pega o ID do usuário autenticado no JWT [cite: 122]
        page=page,
        limit=limit
    )
    
    return OrderHistoryPaginatedResponse(
        success=True,
        data=result["data"],
        total_orders=result["total_orders"],
        total_pages=result["total_pages"],
        page=result["page"],
        limit=result["limit"],
        message="ok"
    )


@users_router.post(
    "/me/enderecos", 
    status_code=status.HTTP_201_CREATED, 
    response_model=AddressOut
)
async def add_address(
    data: AddressCreate, 
    current_user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    
    #Vincula o endereço ao id do usuário do token e salva
    new_address = await user_service.add_address(
        user_id=current_user.id, 
        data=data
    )
    
    return new_address

@users_router.get(
    "/me/enderecos", 
    status_code=status.HTTP_200_OK, 
    response_model=List[AddressOut]
)
async def get_my_addresses(
    current_user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    
    #Busca a lista ordenada
    addresses = await user_service.get_user_addresses(user_id=current_user.id)
    
    return addresses

@users_router.get(
    "/admin/pedidos", 
    status_code=status.HTTP_200_OK, 
    response_model=AdminOrderPaginatedResponse
)
async def get_all_orders_admin(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, description="Itens por página"),
    status: Optional[str] = Query(None, description="Filtrar por status do pedido"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    #Bloqueia se o usuário não for Administrador
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Esta rota é exclusiva para administradores."
        )
        
    user_service = UserService(db)
    
    #Busca todos os pedidos com os filtros aplicados
    result = await user_service.get_all_orders_admin(
        page=page, 
        limit=limit, 
        status_filter=status
    )
    
    return AdminOrderPaginatedResponse(
        success=True,
        data=result["data"],
        total_orders=result["total_orders"],
        total_pages=result["total_pages"],
        page=result["page"],
        limit=result["limit"],
        message="ok"
    )


@users_router.get(
    "/admin/usuarios", 
    status_code=status.HTTP_200_OK, 
    response_model=AdminUserPaginatedResponse
)
async def get_all_customers_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    #Desempacota a tupla se o seu sistema retornar o token junto do usuário
    user_obj = current_user[0] if isinstance(current_user, tuple) else current_user

    #Se não for admin, retorna 403 puro (sem status.HTTP_ para evitar incompatibilidade)
    if user_obj.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Esta rota é exclusiva para administradores."
        )
        
    user_service = UserService(db)
    result = await user_service.get_all_customers_admin(page=page, limit=limit)
    
    return AdminUserPaginatedResponse(
        success=True,
        data=result["data"],
        total_users=result["total_users"],
        total_pages=result["total_pages"],
        page=result["page"],
        limit=result["limit"],
        message="ok"
    )