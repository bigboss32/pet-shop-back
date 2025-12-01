from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from database import get_db
from auth import get_current_user
from models.user import User
from models.sale import Sale, SaleItem
from models.product import Product
from schemas.sale import SaleCreate, SaleResponse, SaleWithUserResponse
from schemas.user import UserSimple
from utils import get_local_now

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    sale: SaleCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Validar productos y stock
    subtotal = 0
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
        subtotal += item.price * item.quantity
    
    # Calcular totales
    total = subtotal - sale.discount
    
    # Crear venta
    new_sale = Sale(
        user_id=current_user.id,
        subtotal=subtotal,
        tax=0,
        discount=sale.discount,
        total=total,
        payment_method=sale.payment_method,
        customer_name=sale.customer_name,
        customer_email=sale.customer_email,
        notes=sale.notes
    )
    db.add(new_sale)
    db.flush()
    
    # Crear items de venta y actualizar stock
    for item in sale.items:
        sale_item = SaleItem(
            sale_id=new_sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price,
            subtotal=item.price * item.quantity
        )
        db.add(sale_item)
        
        # Actualizar stock del producto
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock -= item.quantity
    
    db.commit()
    db.refresh(new_sale)
    return new_sale

@router.get("/", response_model=List[SaleWithUserResponse])
def get_sales(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    today: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale).options(
        joinedload(Sale.user),
        joinedload(Sale.items).joinedload(SaleItem.product)
    )

    # Filtrar por fecha
    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    # Filtrar por día actual
    if today:
        today_date = get_local_now().date()
        start_of_day = datetime.combine(today_date, datetime.min.time()).replace(tzinfo=get_local_now().tzinfo)
        end_of_day = datetime.combine(today_date, datetime.max.time()).replace(tzinfo=get_local_now().tzinfo)
        query = query.filter(Sale.created_at >= start_of_day, Sale.created_at <= end_of_day)

    sales = query.order_by(Sale.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convertir a formato que Pydantic pueda serializar
    result = []
    for sale in sales:
        sale_dict = {
            "id": sale.id,
            "total": sale.total,
            "subtotal": sale.subtotal,
            "tax": sale.tax,
            "discount": sale.discount,
            "payment_method": sale.payment_method,
            "customer_name": sale.customer_name,
            "customer_email": sale.customer_email,
            "notes": sale.notes,
            "created_at": sale.created_at,
            "user": UserSimple(
                id=sale.user.id,
                username=sale.user.username,
                full_name=sale.user.full_name,
                email=sale.user.email
            ) if sale.user else None,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "subtotal": item.subtotal,
                    "product_name": item.product.name if item.product else None
                }
                for item in sale.items
            ]
        }
        result.append(sale_dict)
    
    return result

@router.get("/{sale_id}", response_model=SaleWithUserResponse)
def get_sale(
    sale_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).options(
        joinedload(Sale.user),
        joinedload(Sale.items).joinedload(SaleItem.product)
    ).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Convertir a formato que Pydantic pueda serializar
    sale_response = {
        "id": sale.id,
        "total": sale.total,
        "subtotal": sale.subtotal,
        "tax": sale.tax,
        "discount": sale.discount,
        "payment_method": sale.payment_method,
        "customer_name": sale.customer_name,
        "customer_email": sale.customer_email,
        "notes": sale.notes,
        "created_at": sale.created_at,
        "user": UserSimple(
            id=sale.user.id,
            username=sale.user.username,
            full_name=sale.user.full_name,
            email=sale.user.email
        ) if sale.user else None,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "subtotal": item.subtotal,
                "product_name": item.product.name if item.product else None
            }
            for item in sale.items
        ]
    }
    
    return sale_response

@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina una venta y restaura el stock de los productos.
    Solo disponible para usuarios con rol 'admin'.
    """
    # Verificar que el usuario sea administrador
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar ventas"
        )
    
    # Buscar la venta con sus items
    sale = db.query(Sale).options(
        joinedload(Sale.items)
    ).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    
    # Restaurar el stock de los productos
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
    
    # Eliminar los items de la venta
    for item in sale.items:
        db.delete(item)
    
    # Eliminar la venta
    db.delete(sale)
    db.commit()
    
    return None