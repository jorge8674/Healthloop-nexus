from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Annotated
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from passlib.context import CryptContext
from jose import JWTError, jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = "your-secret-key-health-loop-nexus-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class DietType(str, Enum):
    KETO = "keto"
    MEDITERRANEAN = "mediterranean"
    VEGAN = "vegan"
    HEALTHY = "healthy"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    CLIENT = "client"
    PROFESSIONAL = "professional"

class ProfessionalType(str, Enum):
    NUTRITIONIST = "nutritionist"
    TRAINER = "trainer"

# Models
class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    diet_type: DietType
    image_url: str
    calories: int
    ingredients: List[str]
    allergens: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1
    
class Cart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: UserRole
    password_hash: str
    points: int = 150  # Initial points
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Professional(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    professional_type: ProfessionalType
    specialization: str
    bio: str
    hourly_rate: float = 30.0
    commission_pending: float = 125.0  # Demo commission
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    professional_id: str
    scheduled_date: datetime
    duration_minutes: int = 30
    status: str = "scheduled"
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request Models
class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole
    professional_type: Optional[ProfessionalType] = None
    specialization: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class CartAddRequest(BaseModel):
    product_id: str
    quantity: int = 1

class OrderCreateRequest(BaseModel):
    user_email: str
    user_name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Response Models
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    points: int

class DashboardClientResponse(BaseModel):
    user: UserResponse
    upcoming_appointments: List[dict] = []
    recommended_products: List[Product] = []
    recent_orders: List[Order] = []

class DashboardProfessionalResponse(BaseModel):
    user: UserResponse
    professional_info: dict
    assigned_clients: List[dict] = []
    upcoming_appointments: List[dict] = []
    commission_pending: float = 125.0

# Helper functions
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    if isinstance(item.get('updated_at'), str):
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
    if isinstance(item.get('scheduled_date'), str):
        item['scheduled_date'] = datetime.fromisoformat(item['scheduled_date'])
    return item

# Auth helper functions
def verify_password(plain_password, hashed_password):
    # Ensure password is not too long for bcrypt (max 72 bytes)
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Ensure password is not too long for bcrypt (max 72 bytes)
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**parse_from_mongo(user))

# Initialize demo products and users on startup
demo_products = [
    {
        "name": "Plan Keto Completo",
        "description": "Comida baja en carbohidratos, alta en proteínas y grasas saludables. Perfecta para mantener cetosis.",
        "price": 18.99,
        "diet_type": "keto",
        "image_url": "https://images.unsplash.com/photo-1542814880-7e62cf14b7c8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxrZXRvJTIwZGlldHxlbnwwfHx8fDE3NTg4NDE5Mzd8MA&ixlib=rb-4.1.0&q=85",
        "calories": 450,
        "ingredients": ["Salmón", "Aguacate", "Brócoli", "Aceite de oliva", "Almendras"],
        "allergens": ["Pescado", "Frutos secos"]
    },
    {
        "name": "Bowl Mediterráneo",
        "description": "Inspirado en la dieta mediterránea tradicional con ingredientes frescos y saludables.",
        "price": 16.50,
        "diet_type": "mediterranean",
        "image_url": "https://images.unsplash.com/photo-1653611540493-b3a896319fbf?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxtZWRpdGVycmFuZWFuJTIwZm9vZHxlbnwwfHx8fDE3NTg4NDE5NDJ8MA&ixlib=rb-4.1.0&q=85",
        "calories": 380,
        "ingredients": ["Quinoa", "Garbanzos", "Tomate", "Pepino", "Feta", "Aceitunas"],
        "allergens": ["Lácteos"]
    },
    {
        "name": "Buddha Bowl Vegano",
        "description": "Colorido bowl 100% vegano con proteínas vegetales y superalimentos.",
        "price": 15.75,
        "diet_type": "vegan",
        "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHx2ZWdhbnxlbnwwfHx8fDE3NTg4NDE5NTJ8MA&ixlib=rb-4.1.0&q=85",
        "calories": 320,
        "ingredients": ["Tofu", "Quinoa", "Kale", "Zanahoria", "Hummus", "Semillas de chía"],
        "allergens": ["Soja"]
    },
    {
        "name": "Ensalada Energética",
        "description": "Mezcla perfecta de vegetales frescos, proteínas magras y carbohidratos complejos.",
        "price": 13.25,
        "diet_type": "healthy",
        "image_url": "https://images.unsplash.com/photo-1505253716362-afaea1d3d1af?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxoZWFsdGh5JTIwbWVhbHN8ZW58MHx8fHwxNzU4ODQxOTMyfDA&ixlib=rb-4.1.0&q=85",
        "calories": 285,
        "ingredients": ["Pollo", "Espinaca", "Tomate cherry", "Aguacate", "Nueces"],
        "allergens": ["Frutos secos"]
    },
    {
        "name": "Wrap Keto Supremo",
        "description": "Wrap bajo en carbohidratos con tortilla de coliflor y relleno rico en grasas saludables.",
        "price": 17.99,
        "diet_type": "keto",
        "image_url": "https://images.unsplash.com/photo-1508170754725-6e9a5cfbcabf?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHw0fHxrZXRvJTIwZGlldHxlbnwwfHx8fDE3NTg4NDE5Mzd8MA&ixlib=rb-4.1.0&q=85",
        "calories": 520,
        "ingredients": ["Tortilla de coliflor", "Salmón ahumado", "Queso crema", "Espinaca", "Pepino"],
        "allergens": ["Pescado", "Lácteos"]
    }
]

# API Routes
@api_router.get("/")
async def root():
    return {"message": "HealthLoop Nexus API - Ready!"}

# Auth endpoints
@api_router.post("/auth/register", response_model=Token)
async def register_user(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        password_hash=get_password_hash(user_data.password)
    )
    
    user_dict = prepare_for_mongo(user.dict())
    await db.users.insert_one(user_dict)
    
    # If professional, create professional profile
    if user_data.role == UserRole.PROFESSIONAL and user_data.professional_type:
        professional = Professional(
            user_id=user.id,
            professional_type=user_data.professional_type,
            specialization=user_data.specialization or "General"
        )
        professional_dict = prepare_for_mongo(professional.dict())
        await db.professionals.insert_one(professional_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "points": user.points
        }
    }

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_obj = User(**parse_from_mongo(user))
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_obj.id,
            "email": user_obj.email,
            "name": user_obj.name,
            "role": user_obj.role,
            "points": user_obj.points
        }
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        points=current_user.points
    )

# Dashboard endpoints
@api_router.get("/dashboard/client", response_model=DashboardClientResponse)
async def get_client_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Access forbidden - clients only")
    
    # Get recommended products (first 3)
    products = await db.products.find().to_list(3)
    recommended_products = [Product(**parse_from_mongo(product)) for product in products]
    
    # Get recent orders
    orders = await db.orders.find({"user_id": current_user.id}).sort("created_at", -1).to_list(5)
    recent_orders = [Order(**parse_from_mongo(order)) for order in orders]
    
    # Mock upcoming appointments
    upcoming_appointments = [
        {
            "id": "appt-1",
            "professional_name": "Dr. María García",
            "professional_type": "Nutricionista",
            "date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "duration": 30,
            "status": "scheduled"
        }
    ]
    
    return DashboardClientResponse(
        user=UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            role=current_user.role,
            points=current_user.points
        ),
        upcoming_appointments=upcoming_appointments,
        recommended_products=recommended_products,
        recent_orders=recent_orders
    )

@api_router.get("/dashboard/professional", response_model=DashboardProfessionalResponse)
async def get_professional_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PROFESSIONAL:
        raise HTTPException(status_code=403, detail="Access forbidden - professionals only")
    
    # Get professional info
    professional = await db.professionals.find_one({"user_id": current_user.id})
    if not professional:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    professional_obj = Professional(**parse_from_mongo(professional))
    
    # Mock assigned clients
    assigned_clients = [
        {
            "id": "client-1",
            "name": "María López",
            "objective": "Pérdida de peso",
            "start_date": "2025-01-15",
            "progress": "75%"
        },
        {
            "id": "client-2", 
            "name": "Carlos Ruiz",
            "objective": "Ganar masa muscular",
            "start_date": "2025-02-01",
            "progress": "45%"
        }
    ]
    
    # Mock upcoming appointments
    upcoming_appointments = [
        {
            "id": "appt-prof-1",
            "client_name": "María López",
            "date": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "duration": 30,
            "type": "Follow-up"
        },
        {
            "id": "appt-prof-2",
            "client_name": "Carlos Ruiz",
            "date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration": 30,
            "type": "Initial Consultation"
        }
    ]
    
    return DashboardProfessionalResponse(
        user=UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            role=current_user.role,
            points=current_user.points
        ),
        professional_info={
            "type": professional_obj.professional_type,
            "specialization": professional_obj.specialization,
            "hourly_rate": professional_obj.hourly_rate
        },
        assigned_clients=assigned_clients,
        upcoming_appointments=upcoming_appointments,
        commission_pending=professional_obj.commission_pending
    )

# Products endpoints
@api_router.get("/products", response_model=List[Product])
async def get_products(diet_type: Optional[str] = None):
    query = {}
    if diet_type:
        query["diet_type"] = diet_type
    
    products = await db.products.find(query).to_list(length=None)
    return [Product(**parse_from_mongo(product)) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**parse_from_mongo(product))

# Cart endpoints (now with user authentication)
@api_router.post("/cart/add")
async def add_to_cart(request: CartAddRequest, current_user: User = Depends(get_current_user)):
    # Verify product exists
    product = await db.products.find_one({"id": request.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        cart = Cart(user_id=current_user.id, items=[]).dict()
        cart = prepare_for_mongo(cart)
        await db.carts.insert_one(cart)
    
    # Check if item already exists in cart
    existing_item = None
    for item in cart.get("items", []):
        if item["product_id"] == request.product_id:
            existing_item = item
            break
    
    if existing_item:
        await db.carts.update_one(
            {"user_id": current_user.id, "items.product_id": request.product_id},
            {"$inc": {"items.$.quantity": request.quantity}}
        )
    else:
        new_item = CartItem(product_id=request.product_id, quantity=request.quantity).dict()
        await db.carts.update_one(
            {"user_id": current_user.id},
            {"$push": {"items": new_item}}
        )
    
    return {"message": "Item added to cart successfully"}

@api_router.get("/cart")
async def get_cart(current_user: User = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        return {"items": [], "total": 0}
    
    enriched_items = []
    total = 0
    
    for item in cart.get("items", []):
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            enriched_item = {
                "product": Product(**parse_from_mongo(product)).dict(),
                "quantity": item["quantity"],
                "subtotal": product["price"] * item["quantity"]
            }
            enriched_items.append(enriched_item)
            total += enriched_item["subtotal"]
    
    return {"items": enriched_items, "total": round(total, 2)}

@api_router.delete("/cart/clear")
async def clear_cart(current_user: User = Depends(get_current_user)):
    await db.carts.delete_one({"user_id": current_user.id})
    return {"message": "Cart cleared successfully"}

# Orders endpoints
@api_router.post("/orders", response_model=Order)
async def create_order(current_user: User = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total
    total = 0
    for item in cart["items"]:
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            total += product["price"] * item["quantity"]
    
    # Create order
    order = Order(
        user_id=current_user.id,
        items=cart["items"],
        total_amount=round(total, 2),
        status=OrderStatus.COMPLETED
    ).dict()
    
    order = prepare_for_mongo(order)
    await db.orders.insert_one(order)
    
    # Award points (10 points per dollar spent)
    points_earned = int(total * 10)
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"points": points_earned}}
    )
    
    # Clear cart after order
    await db.carts.delete_one({"user_id": current_user.id})
    
    print(f"📧 Email enviado a {current_user.email}")
    print(f"🎉 Orden #{order['id']} completada exitosamente")
    print(f"🏆 {points_earned} puntos otorgados!")
    
    return Order(**parse_from_mongo(order))

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": current_user.id}).sort("created_at", -1).to_list(length=None)
    return [Order(**parse_from_mongo(order)) for order in orders]

# Initialize database with demo data
@api_router.post("/init-demo-data")
async def init_demo_data():
    # Clear existing data
    await db.products.delete_many({})
    await db.users.delete_many({})
    await db.professionals.delete_many({})
    
    # Insert demo products
    products_to_insert = []
    for product_data in demo_products:
        product = Product(**product_data)
        product_dict = prepare_for_mongo(product.dict())
        products_to_insert.append(product_dict)
    
    await db.products.insert_many(products_to_insert)
    
    # Create demo users
    demo_users = [
        {
            "email": "cliente@healthloop.com",
            "name": "Ana García",
            "password": "demo123",
            "role": UserRole.CLIENT
        },
        {
            "email": "nutricionista@healthloop.com", 
            "name": "Dr. María López",
            "password": "demo123",
            "role": UserRole.PROFESSIONAL,
            "professional_type": ProfessionalType.NUTRITIONIST,
            "specialization": "Nutrición Deportiva"
        },
        {
            "email": "entrenador@healthloop.com",
            "name": "Carlos Fitness",
            "password": "demo123",
            "role": UserRole.PROFESSIONAL,
            "professional_type": ProfessionalType.TRAINER,
            "specialization": "Entrenamiento Funcional"
        }
    ]
    
    for user_data in demo_users:
        user = User(
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            password_hash=get_password_hash(user_data["password"])
        )
        
        user_dict = prepare_for_mongo(user.dict())
        await db.users.insert_one(user_dict)
        
        # Create professional profile if needed
        if user_data["role"] == UserRole.PROFESSIONAL:
            professional = Professional(
                user_id=user.id,
                professional_type=user_data["professional_type"],
                specialization=user_data["specialization"]
            )
            professional_dict = prepare_for_mongo(professional.dict())
            await db.professionals.insert_one(professional_dict)
    
    return {
        "message": f"Initialized {len(demo_products)} products and {len(demo_users)} demo users",
        "demo_accounts": [
            {"email": "cliente@healthloop.com", "password": "demo123", "role": "client"},
            {"email": "nutricionista@healthloop.com", "password": "demo123", "role": "nutritionist"},
            {"email": "entrenador@healthloop.com", "password": "demo123", "role": "trainer"}
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()