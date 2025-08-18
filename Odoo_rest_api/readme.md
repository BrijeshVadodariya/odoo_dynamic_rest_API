# 🚀 Odoo REST API Module

![Odoo Version](https://img.shields.io/badge/Odoo-18.x%20-blue)
![License](https://img.shields.io/badge/License-LGPL--3-blue)

A secure, comprehensive REST API interface for Odoo that enables external systems to interact with Odoo data through standardized HTTP requests.

## 📚 Table of Contents

- [Key Features](#-key-features)
- [Installation](#installation)
- [Usage](#usage)
  - [Authentication (Login to Get Token)](#1-authentication-login-to-get-token)
  - [Calling Protected API Endpoints](#2-calling-protected-api-endpoints)
  - [API Endpoints (Controller Reference)](#3-api-endpoints-controller-reference)
- [Customization](#customization)
- [Example: Full Flow](#example-full-flow)
- [References](#references)
- [License](#license)

---

## 🔑 Key Features

- **Bearer Token Authentication** – Secure API access control
- **Login Endpoint** – Obtain access tokens via user credentials
- **Full CRUD Operations** – Create, Read, Update, Delete records
- **Advanced Search** – Complex domain filters with field selection
- **Model Schema Inspection** – Get field definitions and metadata
- **Method Execution** – Call any Odoo model method
- **JSON-RPC 2.0 Support** – Standardized request/response format
- **Comprehensive Error Handling** – Meaningful error responses

---

## Installation

1. Add the module to your Odoo addons or custom path.
2. Install via the Odoo Apps interface.
3. Restart the Odoo service.

```bash
Example:
cd /path/to/odoo/addons/ or cd /path/to/odoo/custom
git clone https://github.com/your-repo/odoo-rest-api.git
```

---

## Usage

### 1. **Authentication (Login to Get Token)**

Before calling any API endpoint, you must obtain an access token using your Odoo credentials.

- **POST** `/api/login`
- **Headers:**  
  `Content-Type: application/json`
- **Body:**  
  ```json
  {
    "db": "your_db_name",
    "email": "your@email.com",
    "password": "your_password"
  }
  ```
- **Response:**  
  ```json
  {
    "token": "<your_token>",
    "expires_at": "YYYY-MM-DDTHH:MM:SS",
    "user": {
      "id": 1,
      "email": "your@email.com"
    }
  }
  ```

**Example:**
```bash
curl -X POST http://localhost:8069/api/login \
  -H "Content-Type: application/json" \
  -d '{"db": "your_db_name", "email": "admin@example.com", "password": "admin"}'
```

---

### 2. **Calling Protected API Endpoints**

All other endpoints require a Bearer token in the `Authorization` header.  
Use the token received from the login step.

```
Authorization: Bearer <your_token>
```

---

### 3. **API Endpoints (Controller Reference)**

All endpoints below are implemented in `controllers/controllers.py`.  
They require authentication via Bearer token.

#### **Get a Record**
- **GET** `/api/<model>/<id>`
- **Description:** Retrieve a single record by ID.
- **Headers:**  
  `Authorization: Bearer <your_token>`
- **Response:**  
  JSON object with record fields.

**Example:**
```bash
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8069/api/res.partner/7
```

---

#### **Search Records**
- **POST** `/api/<model>/search`
- **Description:** Search for records using Odoo domain filters.
- **Headers:**  
  `Authorization: Bearer <your_token>`  
  `Content-Type: application/json`
- **Body:**  
  JSON-RPC 2.0 format:
  ```json
  {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "domain": [["field", "=", "value"]],
      "limit": 5,
      "order_by": "create_date desc",
      "fields": ["id", "name"]
    }
  }
  ```
- **Response:**  
  List of matching records.

**Example:**
```bash
curl -X POST http://localhost:8069/api/product.product/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "domain": [["type", "=", "consu"]],
      "limit": 5,
      "fields": ["id", "name", "type"]
    }
  }'
```

---

#### **Get Model Schema**
- **GET** `/api/<model>/schema`
- **Description:** Retrieve field definitions and metadata for a model.
- **Headers:**  
  `Authorization: Bearer <your_token>`
- **Response:**  
  JSON object describing fields.

**Example:**
```bash
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8069/api/res.partner/schema
```

---

#### **Create a Record**
- **POST** `/api/<model>/create`
- **Description:** Create a new record.
- **Headers:**  
  `Authorization: Bearer <your_token>`  
  `Content-Type: application/json`
- **Body:**  
  ```json
  {
    "params": {
        "data": {
        "field1": "value1",
        ...
        }
    }
  }
  ```
- **Response:**  
  Created record ID or object.

**Example:**
```bash
curl -X POST http://localhost:8069/api/res.partner/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "params": {
        "data": {
        "field1": "value1",
        ...
        }
    }
  }'
```

---

#### **Update a Record**
- **PUT** `/api/<model>/<id>/update`
- **Description:** Update an existing record.
- **Headers:**  
  `Authorization: Bearer <your_token>`  
  `Content-Type: application/json`
- **Body:**  
  ```json
  {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "data": {
        "field1": "new_value"
        }
    }
  }
  ```
- **Response:**  
  Success status or updated object.

**Example:**
```bash
curl -X PUT http://localhost:8069/api/res.partner/7/update \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
   -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "data": {
        "name": "Orange juice"
      }
    }
  }'
```

---

#### **Delete a Record**
- **DELETE** `/api/<model>/<id>/delete`
- **Description:** Delete a record by ID.
- **Headers:**  
  `Authorization: Bearer <your_token>`
- **Response:**  
  Success status.

**Example:**
```bash
curl -X DELETE http://localhost:8069/api/res.partner/7/delete \
  -H "Authorization: Bearer <your_token>"
```

---

#### **Execute Model Method**
- **POST** `/api/<model>/execute_kw`
- **Description:** Call any model method with arguments.
- **Headers:**  
  `Authorization: Bearer <your_token>`  
  `Content-Type: application/json`
- **Body:**  
  ```json
  {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "method": "search_read",
        "args": [[["is_company", "=", true]]],
        "kwargs": {"fields": ["name", "email"]}
    }
  }
  ```
- **Response:**  
  Method result.

**Example:**
```bash
curl -X POST http://localhost:8069/api.res.partner/execute_kw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
   -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "method": "search_read",
      "args": [[["is_company", "=", true]]],
      "kwargs": {"fields": ["name", "email"]}
    }
   }'
```

---

## Customization

- **Add new endpoints:**  
  Extend `controllers/controllers.py` with new route handlers.
- **Change authentication:**  
  Adjust `authenticate_request()` in `controllers/controllers.py`.
- **Error handling:**  
  All errors are returned as JSON with meaningful messages and HTTP status codes.

---

## Example: Full Flow

1. **Login to get token:**  
   See the "Authentication" section above.
2. **Call any API endpoint:**  
   Pass the token in the `Authorization` header as shown in examples.

---

## References

- [Odoo Documentation](https://www.odoo.com/documentation/)

---

## License

This module is licensed under the