# NexxGate - Backend

## Table of Contents
+ [About](#about)
+ [Live Demo](#demo)

## About <a name = "about"></a>
Backend implementation of NexxGate, implemented in Python using FastAPI. The Database is implemented using PostgreSQL

Running the server on Ubuntu:
```bash
    pip install -r requirements.txt
    screen -S nexxgate
    source env/bin/activate
    uvicorn main:app --host 0.0.0.0 --port 8000
    detach with Ctrl+A, D
```

## Live Demo <a name = "demo"></a>

The backend API is currently being hosted on Render, since AWS Academy shuts down the EC2 instances after a period of inactivity, and can be accessed at [Backend Swagger Docs](
https://nexxgate-backend.onrender.com/nexxgate/api/v1/docs)

The Database is hosted on AWS RDS with PostgreSQL.

![alt text](../../docs/images/backend/swagger.png "Swagger Docs")
