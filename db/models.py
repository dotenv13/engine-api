from sqlalchemy import Column, Integer, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class Engine(Base):
    __tablename__ = 'engines'
    product_id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=True)
    make = Column(Text, nullable=True)
    model = Column(Text, nullable=True)
    year = Column(Text, nullable=True)
    engine_code = Column(Text, nullable=True)
    engine_type = Column(Text, nullable=True)
    price = Column(BigInteger, nullable=True)
    currency = Column(Text, nullable=True)
    stock_text = Column(Text, nullable=True)
    oem = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    images = relationship('EngineImage', back_populates='engine', cascade="all, delete-orphan")

class EngineImage(Base):
    __tablename__ = 'engine_images'
    product_id = Column(Integer, ForeignKey('engines.product_id', ondelete='CASCADE'), primary_key=True)
    image_url = Column(Text, primary_key=True)
    sort_order = Column(Integer, nullable=False, default=0)
    engine = relationship('Engine', back_populates='images')
