from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    email: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Create models for requests
class CartAddRequest(BaseModel):
    product_id: str
    quantity: int = 1

class OrderCreateRequest(BaseModel):
    user_email: str
    user_name: str

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
    return item

# Initialize demo products on startup
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

# Products endpoints
@api_router.get("/products", response_model=List[Product])
async def get_products(diet_type: Optional[str] = None):
    """Get all products, optionally filtered by diet type"""
    query = {}
    if diet_type:
        query["diet_type"] = diet_type
    
    products = await db.products.find(query).to_list(length=None)
    return [Product(**parse_from_mongo(product)) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product by ID"""
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**parse_from_mongo(product))

# Cart endpoints
@api_router.post("/cart/add")
async def add_to_cart(request: CartAddRequest):
    """Add item to cart (session-based for now)"""
    # Verify product exists
    product = await db.products.find_one({"id": request.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # For demo purposes, we'll use a session-based cart
    # In production, this would be user-specific
    session_id = "demo_session"
    
    cart = await db.carts.find_one({"user_id": session_id})
    if not cart:
        cart = Cart(user_id=session_id, items=[]).dict()
        cart = prepare_for_mongo(cart)
        await db.carts.insert_one(cart)
    
    # Check if item already exists in cart
    existing_item = None
    for item in cart.get("items", []):
        if item["product_id"] == request.product_id:
            existing_item = item
            break
    
    if existing_item:
        # Update quantity
        await db.carts.update_one(
            {"user_id": session_id, "items.product_id": request.product_id},
            {"$inc": {"items.$.quantity": request.quantity}}
        )
    else:
        # Add new item
        new_item = CartItem(product_id=request.product_id, quantity=request.quantity).dict()
        await db.carts.update_one(
            {"user_id": session_id},
            {"$push": {"items": new_item}}
        )
    
    return {"message": "Item added to cart successfully"}

@api_router.get("/cart")
async def get_cart():
    """Get current cart with product details"""
    session_id = "demo_session"
    
    cart = await db.carts.find_one({"user_id": session_id})
    if not cart:
        return {"items": [], "total": 0}
    
    # Enrich cart items with product details
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
async def clear_cart():
    """Clear the current cart"""
    session_id = "demo_session"
    await db.carts.delete_one({"user_id": session_id})
    return {"message": "Cart cleared successfully"}

# Orders endpoints
@api_router.post("/orders", response_model=Order)
async def create_order(request: OrderCreateRequest):
    """Create order from current cart (DEMO MODE)"""
    session_id = "demo_session"
    
    # Get current cart
    cart = await db.carts.find_one({"user_id": session_id})
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
        user_id=session_id,
        items=cart["items"],
        total_amount=round(total, 2),
        status=OrderStatus.COMPLETED  # Demo mode - instant completion
    ).dict()
    
    order = prepare_for_mongo(order)
    await db.orders.insert_one(order)
    
    # Clear cart after order
    await db.carts.delete_one({"user_id": session_id})
    
    # Demo notification
    print(f"📧 Email enviado a {request.user_email}")
    print(f"🎉 Orden #{order['id']} completada exitosamente (Demo)")
    
    return Order(**parse_from_mongo(order))

@api_router.get("/orders", response_model=List[Order])
async def get_orders():
    """Get all orders for current session"""
    session_id = "demo_session"
    orders = await db.orders.find({"user_id": session_id}).to_list(length=None)
    return [Order(**parse_from_mongo(order)) for order in orders]

# Initialize database with demo data
@api_router.post("/init-demo-data")
async def init_demo_data():
    """Initialize database with demo products"""
    # Clear existing products
    await db.products.delete_many({})
    
    # Insert demo products
    products_to_insert = []
    for product_data in demo_products:
        product = Product(**product_data)
        product_dict = prepare_for_mongo(product.dict())
        products_to_insert.append(product_dict)
    
    await db.products.insert_many(products_to_insert)
    
    return {"message": f"Initialized {len(demo_products)} demo products"}

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