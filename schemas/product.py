from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(gt=0, decimal_places=2)           # Acepta decimales con 2 cifras
    cost: Decimal = Field(ge=0, default=0, decimal_places=2) # Acepta decimales con 2 cifras
    stock: Decimal = Field(ge=0, default=0, decimal_places=3) # Acepta decimales con 3 cifras
    barcode: Optional[str] = None
    unidad_medida: Optional[str] = None
    category_id: int
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    image_base64: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    stock: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    unidad_medida: Optional[str] = None  # Agregado para poder actualizar
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    is_active: bool
    image_base64: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # Nueva sintaxis de Pydantic v2