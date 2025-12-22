from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from database import Base
from utils import get_local_now

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Numeric(10, 2), nullable=False)  # Cambiado a Numeric para precisión
    cost = Column(Numeric(10, 2), default=0.0)      # Cambiado a Numeric
    stock = Column(Numeric(10, 3), default=0)       # Ahora acepta decimales (ej: 2.500 kg)
    barcode = Column(String, unique=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_base64 = Column(Text, nullable=True)
    unidad_medida = Column(Text, nullable=True)     # "kg", "litros", "unidades", etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_local_now)
    category = relationship("Category", back_populates="products")