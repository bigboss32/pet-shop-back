import base64
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from auth import get_current_user
from models.user import User
from models.product import Product
from models.category import Category
from schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])

# ✅ CREAR PRODUCTO
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    cost: float = Form(0),
    stock: int = Form(0),
    category_id: int = Form(...),
    description: Optional[str] = Form(None),
    barcode: Optional[str] = Form(None),
    unidad_medida: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Verificar categoría
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Verificar código de barras único
    if barcode:
        existing = db.query(Product).filter(Product.barcode == barcode).first()
        if existing:
            raise HTTPException(status_code=400, detail="Barcode already exists")

    # Procesar imagen
    image_base64 = None
    if image:
        contents = await image.read()
        image_base64 = base64.b64encode(contents).decode("utf-8")

    new_product = Product(
        name=name,
        description=description,
        price=price,
        cost=cost,
        stock=stock,
        barcode=barcode,
        category_id=category_id,
        image_base64=image_base64,
        unidad_medida=unidad_medida  # 👈 ESTO FALTABA
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# ✅ LISTAR PRODUCTOS
@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 9999999,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.contains(search))

    products = query.offset(skip).limit(limit).all()

    # 🔹 Convertir imágenes a base64 string legible (ya deberían estar en texto, pero aseguramos)
    for p in products:
        if isinstance(p.image_base64, bytes):
            p.image_base64 = base64.b64encode(p.image_base64).decode("utf-8")
    print(products)
    return products


# ✅ OBTENER PRODUCTO POR ID
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 🔹 Asegurar que la imagen esté en formato base64 string
    if isinstance(product.image_base64, bytes):
        product.image_base64 = base64.b64encode(product.image_base64).decode("utf-8")

    return product

# ✅ ACTUALIZAR PRODUCTO (COMPLETO CON unidad_medida)
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    cost: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    unidad_medida: Optional[str] = Form(None),  # 👈 AGREGAR ESTE PARÁMETRO
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    barcode: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Procesar imagen nueva (si se envía)
    if image:
        contents = await image.read()
        product.image_base64 = base64.b64encode(contents).decode("utf-8")

    # Actualizar otros campos
    if name is not None:
        product.name = name
    if price is not None:
        product.price = price
    if cost is not None:
        product.cost = cost
    if stock is not None:
        product.stock = stock
    if unidad_medida is not None:  # 👈 AGREGAR ESTA ACTUALIZACIÓN
        product.unidad_medida = unidad_medida
    if category_id is not None:
        product.category_id = category_id
    if description is not None:
        product.description = description
    if barcode is not None:
        # Verificar que no haya duplicado
        existing = db.query(Product).filter(Product.barcode == barcode, Product.id != product_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Barcode already exists")
        product.barcode = barcode

    db.commit()
    db.refresh(product)
    return product

# ✅ ELIMINAR (DESACTIVAR) PRODUCTO
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    db.commit()
    return None
