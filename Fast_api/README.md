# Library Management System API

A complete REST API for library management built with FastAPI, PostgreSQL, and SQLAlchemy.

## Features

- **Authors Management**: Create, read, update, and delete authors
- **Publishers Management**: Manage publisher information
- **Categories Management**: Organize books into categories with subcategory support
- **Books Management**: Complete book catalog with complex relationships
- **Members Management**: Library member registration and management
- **Loans Management**: Book lending, returns, renewals, and overdue tracking

## Setup

### Prerequisites

1. **Docker with PostgreSQL**: Make sure you have a PostgreSQL container running
   ```bash
   docker run --name library-db -e POSTGRES_PASSWORD=PASSWORD -e POSTGRES_DB=bookly_db -p 5432:5432 -d postgres:13
   ```

2. **Python 3.8+**: Ensure you have Python installed

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   # Option 1: Direct execution
   python src/app.py
   
   # Option 2: Using uvicorn
   uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authors
- `POST /authors/` - Create a new author
- `GET /authors/` - Get all authors
- `GET /authors/{author_id}` - Get author by ID
- `PUT /authors/{author_id}` - Update author
- `DELETE /authors/{author_id}` - Delete author
- `GET /authors/{author_id}/books` - Get books by author

### Publishers
- `POST /publishers/` - Create a new publisher
- `GET /publishers/` - Get all publishers
- `GET /publishers/{publisher_id}` - Get publisher by ID
- `GET /publishers/{publisher_id}/books` - Get books by publisher

### Categories
- `POST /categories/` - Create a new category
- `GET /categories/` - Get all categories
- `GET /categories/{category_id}` - Get category by ID

### Books
- `POST /books/` - Create a new book
- `GET /books/` - Get all books
- `GET /books/{book_id}` - Get book by ID
- `GET /books/search/` - Search books by title, author, ISBN, or category
- `GET /books/{book_id}/history` - Get loan history for a book

### Members
- `POST /members/` - Create a new member
- `GET /members/` - Get all active members
- `GET /members/{member_id}` - Get member by ID
- `GET /members/email/{email}` - Get member by email
- `GET /members/{member_id}/loans` - Get active loans for a member

### Loans
- `POST /loans/` - Create a new loan (borrow a book)
- `PUT /loans/{loan_id}/return` - Return a book
- `PUT /loans/{loan_id}/renew` - Renew a loan
- `GET /loans/overdue` - Get all overdue loans

### Utility
- `GET /health` - Health check
- `GET /` - API information

## Example Usage

### Create an Author
```bash
curl -X POST "http://localhost:8000/authors/" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "George",
       "last_name": "Orwell",
       "birth_date": "1903-06-25",
       "biography": "English novelist and essayist",
       "nationality": "British"
     }'
```

### Create a Book
```bash
curl -X POST "http://localhost:8000/books/" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "1984",
       "isbn": "978-0-452-28423-4",
       "author_ids": [1],
       "publication_year": 1949,
       "pages": 328,
       "total_copies": 5,
       "price": 12.99
     }'
```

### Search Books
```bash
curl "http://localhost:8000/books/search/?title=1984"
```

## Database Schema

The application automatically creates the following tables:
- `authors` - Author information
- `publishers` - Publisher details
- `categories` - Book categories with hierarchical support
- `books` - Book catalog
- `members` - Library members
- `loans` - Book loans and returns
- `book_authors` - Many-to-many relationship between books and authors
- `book_categories` - Many-to-many relationship between books and categories

## Error Handling

The API includes comprehensive error handling:
- **400 Bad Request**: Invalid input data
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors

## Features

- **Async/Await**: Full asynchronous support for high performance
- **Data Validation**: Pydantic models ensure data integrity
- **Complex Relationships**: Support for many-to-many relationships
- **Auto-Discovery**: Multiple password attempts for database connection
- **Overdue Tracking**: Automatic fine calculation for overdue books
- **Loan Limits**: Member borrowing limits and renewal restrictions
