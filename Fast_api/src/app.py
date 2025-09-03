"""
Complete Library Management System with PostgreSQL + AsyncPG + FastAPI
REST API implementation with complex relationships and CRUD operations
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column, Mapped
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Date, Text, Boolean, select, update, delete
from sqlalchemy.exc import IntegrityError

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Try different passwords - the container might have a different password
POSSIBLE_PASSWORDS = ["PASSWORD", "", "postgres", "password", "admin", "123456"]

# We'll try each password until one works
DATABASE_URLS = [
    f"postgresql+asyncpg://postgres:{pwd}@localhost:5432/bookly_db" 
    for pwd in POSSIBLE_PASSWORDS
]

engine = None
async_session = None

async def find_working_connection():
    """Try different passwords to find the working one"""
    global engine, async_session
    
    for i, url in enumerate(DATABASE_URLS):
        password = POSSIBLE_PASSWORDS[i]
        print(f"   Trying password: {'(empty)' if password == '' else password}")
        
        try:
            test_engine = create_async_engine(url, echo=False)
            async with test_engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            # If we get here, connection worked!
            print(f"✅ Connection successful with password: {'(empty)' if password == '' else password}")
            
            engine = create_async_engine(
                url,
                echo=False,  # Disable SQL logging for API
                pool_size=10,
                max_overflow=0
            )
            async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            return True
            
        except Exception as e:
            await test_engine.dispose()
            print(f"   ❌ Failed: {str(e)[:50]}...")
    
    print("❌ Could not connect with any password. Please check your Docker container.")
    return False

async def get_db():
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    # Startup
    print("🚀 Starting Library Management API...")
    print("🔐 Trying different passwords to connect to Docker PostgreSQL...")
    
    if not await find_working_connection():
        print("❌ Could not establish database connection")
        raise Exception("Database connection failed")
    
    # Create tables
    print("🏗️ Setting up database schema...")
    await create_tables()
    print("✅ Database setup completed!")
    
    yield  # Application runs here
    
    # Shutdown
    print("🧹 Shutting down...")
    if engine:
        await engine.dispose()
    print("👋 API shut down successfully!")

# =============================================================================
# DATABASE MODELS
# =============================================================================

class Base(DeclarativeBase):
    pass

# Association tables for many-to-many relationships
book_author_association = Table(
    'book_authors',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True)
)

book_category_association = Table(
    'book_categories',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)

class Author(Base):
    __tablename__ = 'authors'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    books: Mapped[List["Book"]] = relationship(
        "Book", 
        secondary=book_author_association, 
        back_populates="authors"
    )
    
    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.first_name} {self.last_name}')>"

class Publisher(Base):
    __tablename__ = 'publishers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    books: Mapped[List["Book"]] = relationship("Book", back_populates="publisher")
    
    def __repr__(self):
        return f"<Publisher(id={self.id}, name='{self.name}')>"

class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey('categories.id'), nullable=True)
    
    # Self-referencing relationship for subcategories
    subcategories: Mapped[List["Category"]] = relationship("Category", remote_side=[id])
    
    # Relationships
    books: Mapped[List["Book"]] = relationship(
        "Book", 
        secondary=book_category_association, 
        back_populates="categories"
    )
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Book(Base):
    __tablename__ = 'books'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="English")
    available_copies: Mapped[int] = mapped_column(Integer, default=1)
    total_copies: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[Optional[float]] = mapped_column(nullable=True)
    publisher_id: Mapped[Optional[int]] = mapped_column(ForeignKey('publishers.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    publisher: Mapped[Optional["Publisher"]] = relationship("Publisher", back_populates="books")
    authors: Mapped[List["Author"]] = relationship(
        "Author", 
        secondary=book_author_association, 
        back_populates="books"
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category", 
        secondary=book_category_association, 
        back_populates="books"
    )
    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="book")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"

class Member(Base):
    __tablename__ = 'members'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    membership_date: Mapped[date] = mapped_column(Date, default=date.today)
    membership_type: Mapped[str] = mapped_column(String(50), default="Standard")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_books_allowed: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="member")
    
    def __repr__(self):
        return f"<Member(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"

class Loan(Base):
    __tablename__ = 'loans'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id'), nullable=False)
    loan_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    fine_amount: Mapped[float] = mapped_column(default=0.0)
    renewal_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    book: Mapped["Book"] = relationship("Book", back_populates="loans")
    member: Mapped["Member"] = relationship("Member", back_populates="loans")
    
    def __repr__(self):
        return f"<Loan(id={self.id}, book_id={self.book_id}, member_id={self.member_id}, due_date={self.due_date})>"

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully!")

async def drop_tables():
    """Drop all tables (use with caution)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("⚠️ All tables dropped!")

async def test_connection():
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute("SELECT version()")
            version = result.fetchone()
            print(f"✅ Database connection verified!")
            print(f"PostgreSQL version: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

# =============================================================================
# PYDANTIC MODELS FOR API
# =============================================================================

# Author Models
class AuthorCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    birth_date: Optional[date] = None
    biography: Optional[str] = None
    nationality: Optional[str] = Field(None, max_length=100)

class AuthorResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    birth_date: Optional[date]
    biography: Optional[str]
    nationality: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Publisher Models
class PublisherCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    website: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)

class PublisherResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Category Models
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    
    class Config:
        from_attributes = True

# Book Models
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    isbn: str = Field(..., min_length=1, max_length=20)
    author_ids: List[int] = Field(..., min_items=1)
    publisher_id: Optional[int] = None
    category_ids: Optional[List[int]] = None
    publication_year: Optional[int] = Field(None, gt=0, le=2025)
    pages: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    language: str = "English"
    total_copies: int = Field(1, gt=0)
    price: Optional[float] = Field(None, gt=0)

class BookResponse(BaseModel):
    id: int
    title: str
    isbn: str
    publication_year: Optional[int]
    pages: Optional[int]
    description: Optional[str]
    language: Optional[str]
    available_copies: int
    total_copies: int
    price: Optional[float]
    publisher_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Member Models
class MemberCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    membership_type: str = "Standard"

class MemberResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    date_of_birth: Optional[date]
    membership_date: date
    membership_type: str
    is_active: bool
    max_books_allowed: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Loan Models
class LoanCreate(BaseModel):
    book_id: int = Field(..., gt=0)
    member_id: int = Field(..., gt=0)
    loan_period_days: int = Field(14, gt=0, le=90)

class LoanResponse(BaseModel):
    id: int
    book_id: int
    member_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date]
    is_returned: bool
    fine_amount: float
    renewal_count: int
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# =============================================================================
# CRUD OPERATIONS SERVICE
# =============================================================================

class LibraryService:
    """Complete CRUD service for library management"""
    
    # AUTHOR OPERATIONS
    @staticmethod
    async def create_author(first_name: str, last_name: str, birth_date: Optional[date] = None, 
                           biography: Optional[str] = None, nationality: Optional[str] = None) -> Author:
        async with async_session() as session:
            try:
                author = Author(
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=birth_date,
                    biography=biography,
                    nationality=nationality
                )
                session.add(author)
                await session.commit()
                await session.refresh(author)
                return author
            except IntegrityError as e:
                await session.rollback()
                raise ValueError(f"Author creation failed: {e}")
    
    @staticmethod
    async def get_author(author_id: int) -> Optional[Author]:
        async with async_session() as session:
            result = await session.execute(
                select(Author).where(Author.id == author_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def get_all_authors() -> List[Author]:
        async with async_session() as session:
            result = await session.execute(select(Author).order_by(Author.last_name, Author.first_name))
            return result.scalars().all()
    
    @staticmethod
    async def update_author(author_id: int, **kwargs) -> Optional[Author]:
        async with async_session() as session:
            await session.execute(
                update(Author).where(Author.id == author_id).values(**kwargs)
            )
            await session.commit()
            return await LibraryService.get_author(author_id)
    
    @staticmethod
    async def delete_author(author_id: int) -> bool:
        async with async_session() as session:
            result = await session.execute(delete(Author).where(Author.id == author_id))
            await session.commit()
            return result.rowcount > 0
    
    # PUBLISHER OPERATIONS
    @staticmethod
    async def create_publisher(name: str, address: Optional[str] = None, 
                             website: Optional[str] = None, phone: Optional[str] = None) -> Publisher:
        async with async_session() as session:
            try:
                publisher = Publisher(name=name, address=address, website=website, phone=phone)
                session.add(publisher)
                await session.commit()
                await session.refresh(publisher)
                return publisher
            except IntegrityError as e:
                await session.rollback()
                raise ValueError(f"Publisher creation failed: {e}")
    
    @staticmethod
    async def get_publisher(publisher_id: int) -> Optional[Publisher]:
        async with async_session() as session:
            result = await session.execute(
                select(Publisher).where(Publisher.id == publisher_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def get_all_publishers() -> List[Publisher]:
        async with async_session() as session:
            result = await session.execute(select(Publisher).order_by(Publisher.name))
            return result.scalars().all()
    
    # CATEGORY OPERATIONS
    @staticmethod
    async def create_category(name: str, description: Optional[str] = None, 
                            parent_id: Optional[int] = None) -> Category:
        async with async_session() as session:
            try:
                category = Category(name=name, description=description, parent_id=parent_id)
                session.add(category)
                await session.commit()
                await session.refresh(category)
                return category
            except IntegrityError as e:
                await session.rollback()
                raise ValueError(f"Category creation failed: {e}")
    
    @staticmethod
    async def get_category(category_id: int) -> Optional[Category]:
        async with async_session() as session:
            result = await session.execute(
                select(Category).where(Category.id == category_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def get_all_categories() -> List[Category]:
        async with async_session() as session:
            result = await session.execute(select(Category).order_by(Category.name))
            return result.scalars().all()
    
    # BOOK OPERATIONS
    @staticmethod
    async def create_book(title: str, isbn: str, author_ids: List[int], 
                         publisher_id: Optional[int] = None, category_ids: Optional[List[int]] = None,
                         publication_year: Optional[int] = None, pages: Optional[int] = None,
                         description: Optional[str] = None, language: str = "English",
                         total_copies: int = 1, price: Optional[float] = None) -> Book:
        async with async_session() as session:
            try:
                book = Book(
                    title=title,
                    isbn=isbn,
                    publication_year=publication_year,
                    pages=pages,
                    description=description,
                    language=language,
                    total_copies=total_copies,
                    available_copies=total_copies,
                    price=price,
                    publisher_id=publisher_id
                )
                
                # Add authors
                if author_ids:
                    authors = await session.execute(select(Author).where(Author.id.in_(author_ids)))
                    book.authors.extend(authors.scalars().all())
                
                # Add categories
                if category_ids:
                    categories = await session.execute(select(Category).where(Category.id.in_(category_ids)))
                    book.categories.extend(categories.scalars().all())
                
                session.add(book)
                await session.commit()
                await session.refresh(book)
                return book
            except IntegrityError as e:
                await session.rollback()
                raise ValueError(f"Book creation failed: {e}")
    
    @staticmethod
    async def get_book(book_id: int) -> Optional[Book]:
        async with async_session() as session:
            result = await session.execute(
                select(Book).where(Book.id == book_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def get_all_books() -> List[Book]:
        async with async_session() as session:
            result = await session.execute(select(Book).order_by(Book.title))
            return result.scalars().all()
    
    @staticmethod
    async def search_books(title: Optional[str] = None, author_name: Optional[str] = None,
                          isbn: Optional[str] = None, category_name: Optional[str] = None) -> List[Book]:
        async with async_session() as session:
            query = select(Book)
            
            if title:
                query = query.where(Book.title.ilike(f"%{title}%"))
            
            if isbn:
                query = query.where(Book.isbn.ilike(f"%{isbn}%"))
            
            if author_name:
                query = query.join(book_author_association).join(Author).where(
                    (Author.first_name.ilike(f"%{author_name}%")) | 
                    (Author.last_name.ilike(f"%{author_name}%"))
                )
            
            if category_name:
                query = query.join(book_category_association).join(Category).where(
                    Category.name.ilike(f"%{category_name}%")
                )
            
            result = await session.execute(query.distinct())
            return result.scalars().all()
    
    @staticmethod
    async def get_books_by_author(author_id: int) -> List[Book]:
        async with async_session() as session:
            result = await session.execute(
                select(Book)
                .join(book_author_association)
                .where(book_author_association.c.author_id == author_id)
                .order_by(Book.title)
            )
            return result.scalars().all()
    
    @staticmethod
    async def get_books_by_publisher(publisher_id: int) -> List[Book]:
        async with async_session() as session:
            result = await session.execute(
                select(Book)
                .where(Book.publisher_id == publisher_id)
                .order_by(Book.title)
            )
            return result.scalars().all()
    
    # MEMBER OPERATIONS
    @staticmethod
    async def create_member(first_name: str, last_name: str, email: str, 
                           phone: Optional[str] = None, address: Optional[str] = None,
                           date_of_birth: Optional[date] = None, membership_type: str = "Standard") -> Member:
        async with async_session() as session:
            try:
                member = Member(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    address=address,
                    date_of_birth=date_of_birth,
                    membership_type=membership_type
                )
                session.add(member)
                await session.commit()
                await session.refresh(member)
                return member
            except IntegrityError as e:
                await session.rollback()
                raise ValueError(f"Member creation failed: {e}")
    
    @staticmethod
    async def get_member(member_id: int) -> Optional[Member]:
        async with async_session() as session:
            result = await session.execute(
                select(Member).where(Member.id == member_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def get_all_members() -> List[Member]:
        async with async_session() as session:
            result = await session.execute(
                select(Member).where(Member.is_active == True).order_by(Member.last_name, Member.first_name)
            )
            return result.scalars().all()
    
    @staticmethod
    async def get_member_by_email(email: str) -> Optional[Member]:
        async with async_session() as session:
            result = await session.execute(
                select(Member).where(Member.email == email)
            )
            return result.scalars().first()
    
    # LOAN OPERATIONS
    @staticmethod
    async def create_loan(book_id: int, member_id: int, loan_period_days: int = 14) -> Loan:
        async with async_session() as session:
            try:
                # Check if book is available
                book = await session.get(Book, book_id)
                if not book or book.available_copies <= 0:
                    raise ValueError("Book is not available for loan")
                
                # Check if member is active and hasn't exceeded book limit
                member = await session.get(Member, member_id)
                if not member or not member.is_active:
                    raise ValueError("Member is not active")
                
                active_loans = await session.execute(
                    select(Loan).where(Loan.member_id == member_id, Loan.is_returned == False)
                )
                if len(active_loans.scalars().all()) >= member.max_books_allowed:
                    raise ValueError("Member has reached maximum book limit")
                
                due_date = date.today() + timedelta(days=loan_period_days)
                loan = Loan(
                    book_id=book_id,
                    member_id=member_id,
                    due_date=due_date
                )
                
                # Decrease available copies
                book.available_copies -= 1
                
                session.add(loan)
                await session.commit()
                await session.refresh(loan)
                return loan
            except Exception as e:
                await session.rollback()
                raise e
    
    @staticmethod
    async def return_book(loan_id: int, return_date: Optional[date] = None) -> Loan:
        async with async_session() as session:
            try:
                loan = await session.get(Loan, loan_id)
                if not loan or loan.is_returned:
                    raise ValueError("Invalid loan or already returned")
                
                loan.return_date = return_date or date.today()
                loan.is_returned = True
                
                # Calculate fine if overdue
                if loan.return_date > loan.due_date:
                    overdue_days = (loan.return_date - loan.due_date).days
                    loan.fine_amount = overdue_days * 1.0  # $1 per day fine
                
                # Increase available copies
                book = await session.get(Book, loan.book_id)
                book.available_copies += 1
                
                await session.commit()
                await session.refresh(loan)
                return loan
            except Exception as e:
                await session.rollback()
                raise e
    
    @staticmethod
    async def renew_loan(loan_id: int, additional_days: int = 7) -> Loan:
        async with async_session() as session:
            try:
                loan = await session.get(Loan, loan_id)
                if not loan or loan.is_returned:
                    raise ValueError("Cannot renew returned or invalid loan")
                
                if loan.renewal_count >= 2:  # Max 2 renewals
                    raise ValueError("Maximum renewals exceeded")
                
                loan.due_date = loan.due_date + timedelta(days=additional_days)
                loan.renewal_count += 1
                
                await session.commit()
                await session.refresh(loan)
                return loan
            except Exception as e:
                await session.rollback()
                raise e
    
    @staticmethod
    async def get_active_loans_by_member(member_id: int) -> List[Loan]:
        async with async_session() as session:
            result = await session.execute(
                select(Loan)
                .where(Loan.member_id == member_id)
                .where(Loan.is_returned == False)
                .order_by(Loan.due_date)
            )
            return result.scalars().all()
    
    @staticmethod
    async def get_overdue_loans() -> List[Loan]:
        async with async_session() as session:
            result = await session.execute(
                select(Loan)
                .where(Loan.due_date < date.today())
                .where(Loan.is_returned == False)
                .order_by(Loan.due_date)
            )
            return result.scalars().all()
    
    @staticmethod
    async def get_loan_history_by_book(book_id: int) -> List[Loan]:
        async with async_session() as session:
            result = await session.execute(
                select(Loan)
                .where(Loan.book_id == book_id)
                .order_by(Loan.loan_date.desc())
            )
            return result.scalars().all()

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Library Management System API",
    description="Complete REST API for library management with PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# API ENDPOINTS
# =============================================================================

# AUTHOR ENDPOINTS
@app.post("/authors/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(author: AuthorCreate, db: AsyncSession = Depends(get_db)):
    """Create a new author"""
    try:
        result = await LibraryService.create_author(
            first_name=author.first_name,
            last_name=author.last_name,
            birth_date=author.birth_date,
            biography=author.biography,
            nationality=author.nationality
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/authors/", response_model=List[AuthorResponse])
async def get_all_authors():
    """Get all authors"""
    return await LibraryService.get_all_authors()

@app.get("/authors/{author_id}", response_model=AuthorResponse)
async def get_author(author_id: int):
    """Get author by ID"""
    author = await LibraryService.get_author(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

@app.put("/authors/{author_id}", response_model=AuthorResponse)
async def update_author(author_id: int, author: AuthorCreate):
    """Update author by ID"""
    result = await LibraryService.update_author(author_id, **author.dict(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Author not found")
    return result

@app.delete("/authors/{author_id}")
async def delete_author(author_id: int):
    """Delete author by ID"""
    success = await LibraryService.delete_author(author_id)
    if not success:
        raise HTTPException(status_code=404, detail="Author not found")
    return {"message": "Author deleted successfully"}

# PUBLISHER ENDPOINTS
@app.post("/publishers/", response_model=PublisherResponse, status_code=status.HTTP_201_CREATED)
async def create_publisher(publisher: PublisherCreate):
    """Create a new publisher"""
    try:
        result = await LibraryService.create_publisher(
            name=publisher.name,
            address=publisher.address,
            website=publisher.website,
            phone=publisher.phone
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/publishers/", response_model=List[PublisherResponse])
async def get_all_publishers():
    """Get all publishers"""
    return await LibraryService.get_all_publishers()

@app.get("/publishers/{publisher_id}", response_model=PublisherResponse)
async def get_publisher(publisher_id: int):
    """Get publisher by ID"""
    publisher = await LibraryService.get_publisher(publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return publisher

# CATEGORY ENDPOINTS
@app.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate):
    """Create a new category"""
    try:
        result = await LibraryService.create_category(
            name=category.name,
            description=category.description,
            parent_id=category.parent_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/categories/", response_model=List[CategoryResponse])
async def get_all_categories():
    """Get all categories"""
    return await LibraryService.get_all_categories()

@app.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int):
    """Get category by ID"""
    category = await LibraryService.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# BOOK ENDPOINTS
@app.post("/books/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate):
    """Create a new book"""
    try:
        result = await LibraryService.create_book(
            title=book.title,
            isbn=book.isbn,
            author_ids=book.author_ids,
            publisher_id=book.publisher_id,
            category_ids=book.category_ids,
            publication_year=book.publication_year,
            pages=book.pages,
            description=book.description,
            language=book.language,
            total_copies=book.total_copies,
            price=book.price
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/books/", response_model=List[BookResponse])
async def get_all_books():
    """Get all books"""
    return await LibraryService.get_all_books()

@app.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: int):
    """Get book by ID"""
    book = await LibraryService.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.get("/books/search/", response_model=List[BookResponse])
async def search_books(
    title: Optional[str] = None,
    author_name: Optional[str] = None,
    isbn: Optional[str] = None,
    category_name: Optional[str] = None
):
    """Search books by various criteria"""
    return await LibraryService.search_books(title, author_name, isbn, category_name)

@app.get("/authors/{author_id}/books", response_model=List[BookResponse])
async def get_books_by_author(author_id: int):
    """Get all books by specific author"""
    return await LibraryService.get_books_by_author(author_id)

@app.get("/publishers/{publisher_id}/books", response_model=List[BookResponse])
async def get_books_by_publisher(publisher_id: int):
    """Get all books by specific publisher"""
    return await LibraryService.get_books_by_publisher(publisher_id)

# MEMBER ENDPOINTS
@app.post("/members/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(member: MemberCreate):
    """Create a new member"""
    try:
        result = await LibraryService.create_member(
            first_name=member.first_name,
            last_name=member.last_name,
            email=member.email,
            phone=member.phone,
            address=member.address,
            date_of_birth=member.date_of_birth,
            membership_type=member.membership_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/members/", response_model=List[MemberResponse])
async def get_all_members():
    """Get all active members"""
    return await LibraryService.get_all_members()

@app.get("/members/{member_id}", response_model=MemberResponse)
async def get_member(member_id: int):
    """Get member by ID"""
    member = await LibraryService.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@app.get("/members/email/{email}", response_model=MemberResponse)
async def get_member_by_email(email: str):
    """Get member by email"""
    member = await LibraryService.get_member_by_email(email)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

# LOAN ENDPOINTS
@app.post("/loans/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(loan: LoanCreate):
    """Create a new loan"""
    try:
        result = await LibraryService.create_loan(
            book_id=loan.book_id,
            member_id=loan.member_id,
            loan_period_days=loan.loan_period_days
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/loans/{loan_id}/return", response_model=LoanResponse)
async def return_book(loan_id: int, return_date: Optional[date] = None):
    """Return a book"""
    try:
        result = await LibraryService.return_book(loan_id, return_date)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/loans/{loan_id}/renew", response_model=LoanResponse)
async def renew_loan(loan_id: int, additional_days: int = 7):
    """Renew a loan"""
    try:
        result = await LibraryService.renew_loan(loan_id, additional_days)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/members/{member_id}/loans", response_model=List[LoanResponse])
async def get_member_active_loans(member_id: int):
    """Get active loans for a member"""
    return await LibraryService.get_active_loans_by_member(member_id)

@app.get("/loans/overdue", response_model=List[LoanResponse])
async def get_overdue_loans():
    """Get all overdue loans"""
    return await LibraryService.get_overdue_loans()

@app.get("/books/{book_id}/history", response_model=List[LoanResponse])
async def get_book_loan_history(book_id: int):
    """Get loan history for a specific book"""
    return await LibraryService.get_loan_history_by_book(book_id)

# UTILITY ENDPOINTS
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Library Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "authors": "/authors/",
            "publishers": "/publishers/",
            "categories": "/categories/",
            "books": "/books/",
            "members": "/members/",
            "loans": "/loans/"
        }
    }

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# For running with uvicorn: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    print("="*80)
    print("🏛️  LIBRARY MANAGEMENT SYSTEM API")
    print("📚  FastAPI + PostgreSQL + SQLAlchemy + AsyncPG")
    print("🔄  Full REST API with CRUD Operations")
    print("="*80)
    print("🚀 Starting FastAPI server...")
    print("📖 API Documentation available at: http://localhost:8000/docs")
    
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
