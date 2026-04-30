"""
    Module with models for DB
"""
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import Boolean, ForeignKey, String, DateTime, UUID, UniqueConstraint,func
from sqlalchemy.orm import mapped_column, Mapped, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
   
    """

    Базовый класс от которого наследуются все
    модели таблиц БД

    """
    __abstract__ = True #для того чтобы не создавалась таблица для этого класса


    
               

class RoleEnum(StrEnum):
    
    """
    Список всех ролей в БД
    """
    
    ADMIN = 'admin'
    USER = 'user'


class UserORM(Base):
    
    """
    Модель для всех пользователей системы
    """

    __tablename__ = 'users'

    id: Mapped[uuid.UUID] =  mapped_column(
        UUID, 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    email: Mapped[str] = mapped_column(
        String,
        unique= True,
        nullable= False
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable= False
    )

    role: Mapped[RoleEnum] = mapped_column(
        default= RoleEnum.USER,
        nullable= False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
        )
    
    updated_at : Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now()
        )
    
    profile: Mapped['ProfileORM'] = relationship(
        "ProfileORM",
        back_populates="user",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan"
    )

    oauth_accounts: Mapped['OAuthAccountORM'] = relationship(
        "OAuthAccountORM",
        back_populates="user",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan"
        )

class ProfileORM(Base):
    
    """
    Модель для всех профилей пользователей
    """

    __tablename__ = 'profiles'

    id: Mapped[uuid.UUID] =  mapped_column(
        UUID, 
        primary_key=True, 
        default=uuid.uuid4
    )

    first_name: Mapped[str] = mapped_column(
        String
    )

    last_name: Mapped[str] = mapped_column(
        String
    )

    bio: Mapped[str | None] = mapped_column(
        String(2048)
    )

    avatar_url: Mapped[str| None] = mapped_column(
        String(2048)
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )

    user: Mapped['UserORM'] = relationship(
        "UserORM",
        back_populates="profile",
        uselist=False
    )

class OAuthAccountORM(Base):

    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID]= mapped_column(
        UUID, 
        primary_key=True,
        default= uuid.uuid4
        )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True
    )

    provider: Mapped[str] = mapped_column(
        String,
        nullable=False
        )
    
    provider_user_id: Mapped[str] = mapped_column(
        String(2048), 
        nullable=False,
        )
    
    provider_email: Mapped[str] = mapped_column(
        String, 
        nullable=False
        )
    
    access_token: Mapped[str] = mapped_column(
        String(2048),
        nullable=True
        )
    
    refresh_token: Mapped[str] = mapped_column(
        String(2048), 
        nullable=True
        )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=True
        )
    
    created_at: Mapped[datetime ]= mapped_column(
        DateTime, 
        server_default=func.now()
        )

    user = relationship(
        'UserORM', 
        back_populates="oauth_accounts",
        uselist=False
        )

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id"),
    )
