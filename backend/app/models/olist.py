from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DimCustomer(Base):
    __tablename__ = "dim_customers"

    customer_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer_unique_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    customer_zip_code_prefix: Mapped[str] = mapped_column(String(8), nullable=True)
    customer_city: Mapped[str] = mapped_column(String(128), nullable=True)
    customer_state: Mapped[str] = mapped_column(String(2), nullable=True)


class DimProduct(Base):
    __tablename__ = "dim_products"

    product_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    product_category_name: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    product_weight_g: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    product_length_cm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    product_height_cm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    product_width_cm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)


class DimSeller(Base):
    __tablename__ = "dim_sellers"

    seller_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    seller_zip_code_prefix: Mapped[str] = mapped_column(String(8), nullable=True)
    seller_city: Mapped[str] = mapped_column(String(128), nullable=True)
    seller_state: Mapped[str] = mapped_column(String(2), nullable=True)


class FactOrder(Base):
    __tablename__ = "fact_orders"

    order_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("dim_customers.customer_id"), nullable=False, index=True)
    order_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    order_purchase_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    order_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_delivered_carrier_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_delivered_customer_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_estimated_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    items: Mapped[list["FactOrderItem"]] = relationship(back_populates="order")
    payments: Mapped[list["FactPayment"]] = relationship(back_populates="order")
    reviews: Mapped[list["FactReview"]] = relationship(back_populates="order")


class FactOrderItem(Base):
    __tablename__ = "fact_order_items"

    order_id: Mapped[str] = mapped_column(String(32), ForeignKey("fact_orders.order_id"), primary_key=True)
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(String(32), ForeignKey("dim_products.product_id"), nullable=False, index=True)
    seller_id: Mapped[str] = mapped_column(String(32), ForeignKey("dim_sellers.seller_id"), nullable=False, index=True)
    shipping_limit_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    freight_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["FactOrder"] = relationship(back_populates="items")


class FactPayment(Base):
    __tablename__ = "fact_payments"

    order_id: Mapped[str] = mapped_column(String(32), ForeignKey("fact_orders.order_id"), primary_key=True)
    payment_sequential: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payment_installments: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payment_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["FactOrder"] = relationship(back_populates="payments")


class FactReview(Base):
    __tablename__ = "fact_reviews"

    review_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(32), ForeignKey("fact_orders.order_id"), nullable=False, index=True)
    review_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    review_comment_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_comment_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_creation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_answer_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order: Mapped["FactOrder"] = relationship(back_populates="reviews")
