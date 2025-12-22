from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base
from utils import get_local_now

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Numeric(10, 2), nullable=False)      # Cambiado a Numeric
    subtotal = Column(Numeric(10, 2), nullable=False)   # Cambiado a Numeric
    tax = Column(Numeric(10, 2), default=0.0)           # Cambiado a Numeric
    discount = Column(Numeric(10, 2), default=0.0)      # Cambiado a Numeric
    payment_method = Column(String, nullable=False)     # cash, card, nequi, etc.
    customer_name = Column(String)
    customer_email = Column(String)
    notes = Column(String)
    created_at = Column(DateTime, default=get_local_now)
    
    items = relationship("SaleItem", back_populates="sale")
    user = relationship("User")

class SaleItem(Base):
    __tablename__ = "sale_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Numeric(10, 3), nullable=False)   # Cambiado a Numeric (3 decimales)
    price = Column(Numeric(10, 2), nullable=False)      # Cambiado a Numeric
    subtotal = Column(Numeric(10, 2), nullable=False)   # Cambiado a Numeric
    
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")