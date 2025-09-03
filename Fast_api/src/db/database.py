import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column, Mapped
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Date, Text, Boolean, select, update, delete

# Your Docker PostgreSQL connection with the correct password
DATABASE_URL = "postgresql+asyncpg://yaswanth:mysecurepass@localhost:5432/bookly_db"


print(f"Connecting to Docker PostgreSQL: localhost:5432/bookly_db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=10,
    max_overflow=0
)

# Create session factory
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    books: Mapped[List["Book"]] = relationship(
        "Book", 
        secondary=book_author_association, 
        back_populates="authors"
    )

class Publisher(Base):
    __tablename__ = 'publishers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    books: Mapped[List["Book"]] = relationship("Book", back_populates="publisher")

class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    books: Mapped[List["Book"]] = relationship(
        "Book", 
        secondary=book_category_association, 
        back_populates="categories"
    )

class Book(Base):
    __tablename__ = 'books'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    available_copies: Mapped[int] = mapped_column(Integer, default=1)
    total_copies: Mapped[int] = mapped_column(Integer, default=1)
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

class Member(Base):
    __tablename__ = 'members'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    membership_date: Mapped[date] = mapped_column(Date, default=date.today)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="member")

class Loan(Base):
    __tablename__ = 'loans'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id'), nullable=False)
    loan_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    fine_amount: Mapped[Optional[float]] = mapped_column(nullable=True, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    book: Mapped["Book"] = relationship("Book", back_populates="loans")
    member: Mapped["Member"] = relationship("Member", back_populates="loans")

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
            print(f"✅ Successfully connected to Docker PostgreSQL!")
            print(f"PostgreSQL version: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


class LibraryService:
    """Service class for all CRUD operations"""
    
    # AUTHOR CRUD OPERATIONS
    @staticmethod
    async def create_author(first_name: str, last_name: str, birth_date: Optional[date] = None, biography: Optional[str] = None):
        async with async_session() as session:
            author = Author(
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                biography=biography
            )
            session.add(author)
            await session.commit()
            await session.refresh(author)
            return author
    
    @staticmethod
    async def get_author(author_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(Author).where(Author.id == author_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def get_all_authors():
        async with async_session() as session:
            result = await session.execute(select(Author))
            return result.scalars().all()
    
    @staticmethod
    async def update_author(author_id: int, **kwargs):
        async with async_session() as session:
            await session.execute(
                update(Author).where(Author.id == author_id).values(**kwargs)
            )
            await session.commit()
            return await LibraryService.get_author(author_id)
    
    @staticmethod
    async def delete_author(author_id: int):
        async with async_session() as session:
            await session.execute(delete(Author).where(Author.id == author_id))
            await session.commit()
    
    # PUBLISHER CRUD OPERATIONS
    @staticmethod
    async def create_publisher(name: str, address: Optional[str] = None, website: Optional[str] = None):
        async with async_session() as session:
            publisher = Publisher(name=name, address=address, website=website)
            session.add(publisher)
            await session.commit()
            await session.refresh(publisher)
            return publisher
    
    @staticmethod
    async def get_publisher(publisher_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(Publisher).where(Publisher.id == publisher_id)
            )
            return result.scalars().first()
    
    # CATEGORY CRUD OPERATIONS
    @staticmethod
    async def create_category(name: str, description: Optional[str] = None):
        async with async_session() as session:
            category = Category(name=name, description=description)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            return category
    
    @staticmethod
    async def get_category(category_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(Category).where(Category.id == category_id)
            )
            return result.scalars().first()
    
    # BOOK CRUD OPERATIONS
    @staticmethod
    async def create_book(title: str, isbn: str, author_ids: List[int], 
                         publisher_id: Optional[int] = None, category_ids: Optional[List[int]] = None,
                         publication_year: Optional[int] = None, pages: Optional[int] = None,
                         description: Optional[str] = None, total_copies: int = 1):
        async with async_session() as session:
            book = Book(
                title=title,
                isbn=isbn,
                publication_year=publication_year,
                pages=pages,
                description=description,
                total_copies=total_copies,
                available_copies=total_copies,
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
    
    @staticmethod
    async def get_book(book_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(Book).where(Book.id == book_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def search_books(title: Optional[str] = None, author_name: Optional[str] = None):
        async with async_session() as session:
            query = select(Book)
            
            if title:
                query = query.where(Book.title.ilike(f"%{title}%"))
            
            if author_name:
                query = query.join(book_author_association).join(Author).where(
                    (Author.first_name.ilike(f"%{author_name}%")) | 
                    (Author.last_name.ilike(f"%{author_name}%"))
                )
            
            result = await session.execute(query)
            return result.scalars().all()
    
    # MEMBER CRUD OPERATIONS
    @staticmethod
    async def create_member(first_name: str, last_name: str, email: str, 
                           phone: Optional[str] = None, address: Optional[str] = None):
        async with async_session() as session:
            member = Member(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address
            )
            session.add(member)
            await session.commit()
            await session.refresh(member)
            return member
    
    @staticmethod
    async def get_member(member_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(Member).where(Member.id == member_id)
            )
            return result.scalars().first()
    
    # LOAN CRUD OPERATIONS
    @staticmethod
    async def create_loan(book_id: int, member_id: int, loan_period_days: int = 14):
        async with async_session() as session:
            # Check if book is available
            book = await session.get(Book, book_id)
            if not book or book.available_copies <= 0:
                raise ValueError("Book is not available for loan")
            
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
    
    @staticmethod
    async def return_book(loan_id: int, return_date: Optional[date] = None):
        async with async_session() as session:
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
    
    @staticmethod
    async def get_overdue_loans():
        async with async_session() as session:
            result = await session.execute(
                select(Loan)
                .where(Loan.due_date < date.today())
                .where(Loan.is_returned == False)
            )
            return result.scalars().all()
async def main():
    """Main function to demonstrate the library system"""
    print("🚀 Starting Library Management System...")
    
    # Test connection
    if not await test_connection():
        return
    
    # Create tables
    await create_tables()
    
    try:
        # Create some sample data
        print("\n📝 Creating sample data...")
        
        # Create authors
        author1 = await LibraryService.create_author("George", "Orwell", date(1903, 6, 25), "British author")
        author2 = await LibraryService.create_author("Jane", "Austen", date(1775, 12, 16), "English novelist")
        print(f"✅ Created authors: {author1.first_name} {author1.last_name}, {author2.first_name} {author2.last_name}")
        
        # Create publisher
        publisher = await LibraryService.create_publisher("Penguin Classics", "London, UK", "https://penguin.co.uk")
        print(f"✅ Created publisher: {publisher.name}")
        
        # Create categories
        fiction = await LibraryService.create_category("Fiction", "Fictional literature")
        classic = await LibraryService.create_category("Classic", "Classic literature")
        print(f"✅ Created categories: {fiction.name}, {classic.name}")
        
        # Create books
        book1 = await LibraryService.create_book(
            title="1984",
            isbn="978-0-452-28423-4",
            author_ids=[author1.id],
            publisher_id=publisher.id,
            category_ids=[fiction.id, classic.id],
            publication_year=1949,
            pages=328,
            description="A dystopian social science fiction novel",
            total_copies=5
        )
        
        book2 = await LibraryService.create_book(
            title="Pride and Prejudice",
            isbn="978-0-14-143951-8",
            author_ids=[author2.id],
            publisher_id=publisher.id,
            category_ids=[fiction.id, classic.id],
            publication_year=1813,
            pages=432,
            total_copies=3
        )
        print(f"✅ Created books: '{book1.title}', '{book2.title}'")
        
        # Create member
        member = await LibraryService.create_member(
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com",
            phone="123-456-7890",
            address="123 Main St, City"
        )
        print(f"✅ Created member: {member.first_name} {member.last_name}")
        
        # Create loan
        loan = await LibraryService.create_loan(book1.id, member.id, loan_period_days=14)
        print(f"✅ Created loan: '{book1.title}' to {member.first_name} {member.last_name}")
        print(f"   📅 Due date: {loan.due_date}")
        
        # Search functionality
        print("\n🔍 Testing search functionality...")
        search_results = await LibraryService.search_books(title="1984")
        print(f"✅ Found {len(search_results)} books matching '1984'")
        
        search_results = await LibraryService.search_books(author_name="Orwell")
        print(f"✅ Found {len(search_results)} books by author 'Orwell'")
        
        # Return book
        print("\n📖 Testing book return...")
        await LibraryService.return_book(loan.id)
        print("✅ Book returned successfully")
        
        # Check overdue loans
        overdue = await LibraryService.get_overdue_loans()
        print(f"✅ Found {len(overdue)} overdue loans")
        
        print("\n🎉 Library Management System setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
