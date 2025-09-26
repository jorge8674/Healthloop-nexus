from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Annotated
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
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
security = HTTPBearer()

# Helper functions for MongoDB serialization
def parse_from_mongo(item):
    """Parse MongoDB document to Python dict, handling special types"""
    if isinstance(item.get('date'), str):
        try:
            item['date'] = datetime.fromisoformat(item['date']).date()
        except:
            pass
    if isinstance(item.get('time'), str):
        try:
            item['time'] = datetime.strptime(item['time'], '%H:%M:%S').time()
        except:
            pass
    if isinstance(item.get('created_at'), str):
        try:
            item['created_at'] = datetime.fromisoformat(item['created_at'])
        except:
            pass
    return item

def prepare_for_mongo(data):
    """Prepare Python data for MongoDB storage"""
    if hasattr(data, 'dict'):
        data = data.dict()
    
    if isinstance(data.get('date'), str):
        data['date'] = data['date']
    if isinstance(data.get('time'), str):
        data['time'] = data['time'] 
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    
    return data

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

class MembershipLevel(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ELITE = "elite"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class ConsentLevel(str, Enum):
    BASIC = "basic"
    COMPLETE = "complete"
    COMPLETE_WITH_ANALYTICS = "complete_with_analytics"

class PointAction(str, Enum):
    REGISTRATION = "registration"
    FIRST_PURCHASE = "first_purchase"
    PURCHASE = "purchase"
    SCHEDULE_CONSULTATION = "schedule_consultation"
    COMPLETE_PROFILE = "complete_profile"
    REFER_FRIEND = "refer_friend"
    COMPLETE_CONSULTATION = "complete_consultation"
    VIDEO_COMPLETION = "video_completion"

class BadgeType(str, Enum):
    BEGINNER = "beginner"
    ACTIVE = "active"
    PREMIUM = "premium"
    ELITE = "elite"

class ConsultationStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Points configuration
POINT_VALUES = {
    PointAction.REGISTRATION: 100,
    PointAction.FIRST_PURCHASE: 200,
    PointAction.PURCHASE: 10,  # Per dollar spent
    PointAction.SCHEDULE_CONSULTATION: 150,
    PointAction.COMPLETE_PROFILE: 50,
    PointAction.REFER_FRIEND: 300,
    PointAction.COMPLETE_CONSULTATION: 200,
    PointAction.VIDEO_COMPLETION: 50
}

BADGE_THRESHOLDS = {
    BadgeType.BEGINNER: 0,
    BadgeType.ACTIVE: 500,
    BadgeType.PREMIUM: 1500,
    BadgeType.ELITE: 5000
}

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
    total_points_earned: int = 150
    level: str = "Beginner"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PointsTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: PointAction
    points: int
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Badge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    badge_type: BadgeType
    earned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConsultationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    professional_id: str
    status: ConsultationStatus = ConsultationStatus.SCHEDULED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: int = 30
    notes: str = ""
    recommendations: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Professional(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    professional_type: ProfessionalType
    specialization: str
    bio: str
    hourly_rate: float = 30.0
    commission_pending: float = 125.0  # Demo commission
    total_earnings: float = 850.0
    active_consultations: int = 0
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

class PointsAddRequest(BaseModel):
    action: PointAction
    description: Optional[str] = None
    amount_spent: Optional[float] = None  # For purchase-based points

class ConsultationStartRequest(BaseModel):
    client_id: str

class ConsultationCompleteRequest(BaseModel):
    consultation_id: str
    notes: str
    recommendations: str

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
    total_points_earned: int
    level: str

class PointsHistoryResponse(BaseModel):
    transactions: List[PointsTransaction]
    total_points: int
    current_level: str
    next_level_threshold: int
    progress_percentage: float

class LeaderboardEntry(BaseModel):
    name: str
    points: int
    level: str
    rank: int

class DashboardClientResponse(BaseModel):
    user: UserResponse
    upcoming_appointments: List[dict] = []
    recommended_products: List[Product] = []
    recent_orders: List[Order] = []
    recent_points: List[PointsTransaction] = []
    badges: List[Badge] = []

class DashboardProfessionalResponse(BaseModel):
    user: UserResponse
    professional_info: dict
    assigned_clients: List[dict] = []
    upcoming_appointments: List[dict] = []
    commission_pending: float = 125.0
    total_earnings: float = 850.0
    active_consultations: List[ConsultationSession] = []

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
    if isinstance(item.get('start_time'), str):
        item['start_time'] = datetime.fromisoformat(item['start_time'])
    if isinstance(item.get('end_time'), str):
        item['end_time'] = datetime.fromisoformat(item['end_time'])
    if isinstance(item.get('earned_at'), str):
        item['earned_at'] = datetime.fromisoformat(item['earned_at'])
    return item

# Auth helper functions
def verify_password(plain_password, hashed_password):
    # Simple hash comparison using SHA256
    password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return password_hash == hashed_password

def get_password_hash(password):
    # Simple SHA256 hash
    return hashlib.sha256(password.encode()).hexdigest()

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

# Points system helper functions
def calculate_level(total_points):
    if total_points >= 5000:
        return "Elite"
    elif total_points >= 1500:
        return "Premium"
    elif total_points >= 500:
        return "Active"
    else:
        return "Beginner"

def get_next_level_threshold(current_level):
    thresholds = {
        "Beginner": 500,
        "Active": 1500,
        "Premium": 5000,
        "Elite": 10000
    }
    return thresholds.get(current_level, 10000)

async def award_points(user_id: str, action: PointAction, description: str = None, amount_spent: float = None):
    """Award points to user for specific actions"""
    if action == PointAction.PURCHASE and amount_spent:
        points = int(amount_spent * POINT_VALUES[PointAction.PURCHASE])
    else:
        points = POINT_VALUES.get(action, 0)
    
    if points > 0:
        # Create points transaction
        transaction = PointsTransaction(
            user_id=user_id,
            action=action,
            points=points,
            description=description or f"Points earned for {action.value}"
        )
        
        transaction_dict = prepare_for_mongo(transaction.dict())
        await db.points_transactions.insert_one(transaction_dict)
        
        # Update user points
        await db.users.update_one(
            {"id": user_id},
            {
                "$inc": {
                    "points": points,
                    "total_points_earned": points
                }
            }
        )
        
        # Update user level
        user = await db.users.find_one({"id": user_id})
        new_level = calculate_level(user["total_points_earned"])
        if user["level"] != new_level:
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"level": new_level}}
            )
            
            # Award badge if needed
            await award_badge_if_eligible(user_id, new_level)
        
        print(f"🏆 {points} puntos otorgados a usuario {user_id} por {action.value}")
        return points
    return 0

async def award_badge_if_eligible(user_id: str, level: str):
    """Award badge based on user level"""
    badge_mapping = {
        "Active": BadgeType.ACTIVE,
        "Premium": BadgeType.PREMIUM,
        "Elite": BadgeType.ELITE
    }
    
    badge_type = badge_mapping.get(level)
    if badge_type:
        # Check if user already has this badge
        existing_badge = await db.badges.find_one({
            "user_id": user_id,
            "badge_type": badge_type
        })
        
        if not existing_badge:
            badge = Badge(user_id=user_id, badge_type=badge_type)
            badge_dict = prepare_for_mongo(badge.dict())
            await db.badges.insert_one(badge_dict)
            print(f"🎖️ Badge {badge_type.value} otorgado a usuario {user_id}")

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
            specialization=user_data.specialization or "General",
            bio=f"Especialista en {user_data.specialization or 'General'}"
        )
        professional_dict = prepare_for_mongo(professional.dict())
        await db.professionals.insert_one(professional_dict)
    
    # Award registration points
    await award_points(user.id, PointAction.REGISTRATION, "Bienvenido a HealthLoop Nexus!")
    
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
            "points": user.points + POINT_VALUES[PointAction.REGISTRATION],
            "total_points_earned": user.total_points_earned + POINT_VALUES[PointAction.REGISTRATION],
            "level": calculate_level(user.total_points_earned + POINT_VALUES[PointAction.REGISTRATION])
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
            "points": user_obj.points,
            "total_points_earned": user_obj.total_points_earned,
            "level": user_obj.level
        }
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        points=current_user.points,
        total_points_earned=current_user.total_points_earned,
        level=current_user.level
    )

# Points system endpoints
@api_router.post("/points/add")
async def add_points(request: PointsAddRequest, current_user: User = Depends(get_current_user)):
    """Add points to user account for specific actions"""
    description = request.description or f"Points earned for {request.action.value}"
    points_awarded = await award_points(current_user.id, request.action, description, request.amount_spent)
    
    return {
        "message": f"¡{points_awarded} puntos agregados!",
        "points_awarded": points_awarded,
        "action": request.action
    }

@api_router.get("/points/history", response_model=PointsHistoryResponse)
async def get_points_history(current_user: User = Depends(get_current_user)):
    """Get user's points history and progress"""
    # Get recent transactions
    transactions = await db.points_transactions.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).to_list(20)
    
    transactions_list = [PointsTransaction(**parse_from_mongo(t)) for t in transactions]
    
    # Calculate progress to next level
    current_threshold = get_next_level_threshold(current_user.level)
    
    if current_user.level == "Elite":
        progress_percentage = 100
    else:
        previous_threshold = BADGE_THRESHOLDS.get(BadgeType(current_user.level.lower()), 0)
        progress_percentage = min(100, ((current_user.total_points_earned - previous_threshold) / (current_threshold - previous_threshold)) * 100)
    
    return PointsHistoryResponse(
        transactions=transactions_list,
        total_points=current_user.points,
        current_level=current_user.level,
        next_level_threshold=current_threshold,
        progress_percentage=round(progress_percentage, 1)
    )

@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get top users leaderboard"""
    users = await db.users.find().sort("total_points_earned", -1).limit(10).to_list(10)
    
    leaderboard = []
    for i, user_data in enumerate(users):
        leaderboard.append(LeaderboardEntry(
            name=user_data["name"],
            points=user_data["total_points_earned"],
            level=user_data["level"],
            rank=i + 1
        ))
    
    return {"leaderboard": leaderboard}

@api_router.get("/badges")
async def get_user_badges(current_user: User = Depends(get_current_user)):
    """Get user's earned badges"""
    badges = await db.badges.find({"user_id": current_user.id}).to_list(length=None)
    return {"badges": [Badge(**parse_from_mongo(badge)) for badge in badges]}

# Consultation endpoints
@api_router.post("/consultations/start")
async def start_consultation(request: ConsultationStartRequest, current_user: User = Depends(get_current_user)):
    """Start a new consultation session"""
    if current_user.role != UserRole.PROFESSIONAL:
        raise HTTPException(status_code=403, detail="Only professionals can start consultations")
    
    # Create consultation session
    consultation = ConsultationSession(
        client_id=request.client_id,
        professional_id=current_user.id,
        status=ConsultationStatus.IN_PROGRESS,
        start_time=datetime.now(timezone.utc)
    )
    
    consultation_dict = prepare_for_mongo(consultation.dict())
    await db.consultations.insert_one(consultation_dict)
    
    # Update professional active consultations
    await db.professionals.update_one(
        {"user_id": current_user.id},
        {"$inc": {"active_consultations": 1}}
    )
    
    return {
        "message": "Consulta iniciada exitosamente",
        "consultation_id": consultation.id,
        "start_time": consultation.start_time,
        "duration_minutes": consultation.duration_minutes
    }

@api_router.put("/consultations/complete")
async def complete_consultation(request: ConsultationCompleteRequest, current_user: User = Depends(get_current_user)):
    """Complete a consultation with notes and recommendations"""
    if current_user.role != UserRole.PROFESSIONAL:
        raise HTTPException(status_code=403, detail="Only professionals can complete consultations")
    
    # Update consultation
    await db.consultations.update_one(
        {"id": request.consultation_id, "professional_id": current_user.id},
        {
            "$set": {
                "status": ConsultationStatus.COMPLETED,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "notes": request.notes,
                "recommendations": request.recommendations
            }
        }
    )
    
    # Get consultation to award points to client
    consultation = await db.consultations.find_one({"id": request.consultation_id})
    if consultation:
        # Award points to client
        await award_points(
            consultation["client_id"], 
            PointAction.COMPLETE_CONSULTATION, 
            f"Consulta completada con {current_user.name}"
        )
        
        # Update professional stats
        await db.professionals.update_one(
            {"user_id": current_user.id},
            {
                "$inc": {
                    "active_consultations": -1,
                    "total_earnings": 30.0  # Add consultation fee
                }
            }
        )
    
    return {
        "message": "Consulta completada exitosamente",
        "points_awarded_to_client": POINT_VALUES[PointAction.COMPLETE_CONSULTATION]
    }

@api_router.get("/consultations/active")
async def get_active_consultations(current_user: User = Depends(get_current_user)):
    """Get active consultations for professional"""
    if current_user.role != UserRole.PROFESSIONAL:
        raise HTTPException(status_code=403, detail="Only professionals can view consultations")
    
    consultations = await db.consultations.find({
        "professional_id": current_user.id,
        "status": ConsultationStatus.IN_PROGRESS
    }).to_list(length=None)
    
    return {
        "active_consultations": [ConsultationSession(**parse_from_mongo(c)) for c in consultations]
    }

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
    
    # Get recent points
    recent_points = await db.points_transactions.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).to_list(5)
    recent_points_list = [PointsTransaction(**parse_from_mongo(t)) for t in recent_points]
    
    # Get badges
    badges = await db.badges.find({"user_id": current_user.id}).to_list(length=None)
    badges_list = [Badge(**parse_from_mongo(badge)) for badge in badges]
    
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
            points=current_user.points,
            total_points_earned=current_user.total_points_earned,
            level=current_user.level
        ),
        upcoming_appointments=upcoming_appointments,
        recommended_products=recommended_products,
        recent_orders=recent_orders,
        recent_points=recent_points_list,
        badges=badges_list
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
    
    # Get active consultations
    active_consultations = await db.consultations.find({
        "professional_id": current_user.id,
        "status": ConsultationStatus.IN_PROGRESS
    }).to_list(length=None)
    
    active_consultations_list = [ConsultationSession(**parse_from_mongo(c)) for c in active_consultations]
    
    # Mock assigned clients with enhanced data
    assigned_clients = [
        {
            "id": "client-1",
            "name": "María López",
            "objective": "Pérdida de peso",
            "start_date": "2025-01-15",
            "progress": "75%",
            "points": 850,
            "level": "Active",
            "last_consultation": "2025-09-20"
        },
        {
            "id": "client-2", 
            "name": "Carlos Ruiz",
            "objective": "Ganar masa muscular",
            "start_date": "2025-02-01",
            "progress": "45%",
            "points": 420,
            "level": "Beginner",
            "last_consultation": "2025-09-18"
        }
    ]
    
    # Mock upcoming appointments
    upcoming_appointments = [
        {
            "id": "appt-prof-1",
            "client_name": "María López",
            "client_points": 850,
            "date": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "duration": 30,
            "type": "Follow-up"
        },
        {
            "id": "appt-prof-2",
            "client_name": "Carlos Ruiz",
            "client_points": 420,
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
            points=current_user.points,
            total_points_earned=current_user.total_points_earned,
            level=current_user.level
        ),
        professional_info={
            "type": professional_obj.professional_type,
            "specialization": professional_obj.specialization,
            "hourly_rate": professional_obj.hourly_rate
        },
        assigned_clients=assigned_clients,
        upcoming_appointments=upcoming_appointments,
        commission_pending=professional_obj.commission_pending,
        total_earnings=professional_obj.total_earnings,
        active_consultations=active_consultations_list
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
    
    # Check if this is first purchase
    existing_orders = await db.orders.count_documents({"user_id": current_user.id})
    
    # Create order
    order = Order(
        user_id=current_user.id,
        items=cart["items"],
        total_amount=round(total, 2),
        status=OrderStatus.COMPLETED
    ).dict()
    
    order = prepare_for_mongo(order)
    await db.orders.insert_one(order)
    
    # Award points based on purchase
    if existing_orders == 0:
        # First purchase bonus
        await award_points(current_user.id, PointAction.FIRST_PURCHASE, "¡Primera compra completada!")
    
    # Award points for amount spent
    await award_points(current_user.id, PointAction.PURCHASE, f"Compra por ${total}", total)
    
    # Clear cart after order
    await db.carts.delete_one({"user_id": current_user.id})
    
    print(f"📧 Email enviado a {current_user.email}")
    print(f"🎉 Orden #{order['id']} completada exitosamente")
    
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
    await db.points_transactions.delete_many({})
    await db.badges.delete_many({})
    
    # Insert demo products
    products_to_insert = []
    for product_data in demo_products:
        product = Product(**product_data)
        product_dict = prepare_for_mongo(product.dict())
        products_to_insert.append(product_dict)
    
    await db.products.insert_many(products_to_insert)
    
    # Create demo users with enhanced data
    demo_users = [
        {
            "email": "cliente@healthloop.com",
            "name": "Ana García",
            "password": "demo123",
            "role": UserRole.CLIENT,
            "points": 650,
            "total_points_earned": 1200,
            "level": "Active"
        },
        {
            "email": "nutricionista@healthloop.com", 
            "name": "Dr. María López",
            "password": "demo123",
            "role": UserRole.PROFESSIONAL,
            "professional_type": ProfessionalType.NUTRITIONIST,
            "specialization": "Nutrición Deportiva",
            "points": 300,
            "total_points_earned": 800,
            "level": "Active"
        },
        {
            "email": "entrenador@healthloop.com",
            "name": "Carlos Fitness",
            "password": "demo123",
            "role": UserRole.PROFESSIONAL,
            "professional_type": ProfessionalType.TRAINER,
            "specialization": "Entrenamiento Funcional",
            "points": 150,
            "total_points_earned": 400,
            "level": "Beginner"
        }
    ]
    
    for user_data in demo_users:
        user = User(
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            password_hash=get_password_hash(user_data["password"]),
            points=user_data.get("points", 150),
            total_points_earned=user_data.get("total_points_earned", 150),
            level=user_data.get("level", "Beginner")
        )
        
        user_dict = prepare_for_mongo(user.dict())
        await db.users.insert_one(user_dict)
        
        # Create professional profile if needed
        if user_data["role"] == UserRole.PROFESSIONAL:
            professional = Professional(
                user_id=user.id,
                professional_type=user_data["professional_type"],
                specialization=user_data["specialization"],
                bio=f"Especialista en {user_data['specialization']}"
            )
            professional_dict = prepare_for_mongo(professional.dict())
            await db.professionals.insert_one(professional_dict)
        
        # Add demo points transactions
        demo_transactions = [
            {"action": PointAction.REGISTRATION, "points": 100, "description": "Registro completado"},
            {"action": PointAction.COMPLETE_PROFILE, "points": 50, "description": "Perfil completado"},
            {"action": PointAction.FIRST_PURCHASE, "points": 200, "description": "Primera compra"},
        ]
        
        for transaction_data in demo_transactions:
            if user_data.get("total_points_earned", 0) >= sum(t["points"] for t in demo_transactions):
                transaction = PointsTransaction(
                    user_id=user.id,
                    action=transaction_data["action"],
                    points=transaction_data["points"],
                    description=transaction_data["description"]
                )
                transaction_dict = prepare_for_mongo(transaction.dict())
                await db.points_transactions.insert_one(transaction_dict)
        
        # Award badges based on level
        if user.level in ["Active", "Premium", "Elite"]:
            badge = Badge(
                user_id=user.id,
                badge_type=BadgeType.ACTIVE if user.level == "Active" else BadgeType.PREMIUM if user.level == "Premium" else BadgeType.ELITE
            )
            badge_dict = prepare_for_mongo(badge.dict())
            await db.badges.insert_one(badge_dict)
    
    return {
        "message": f"Initialized {len(demo_products)} products, {len(demo_users)} demo users with points system",
        "demo_accounts": [
            {"email": "cliente@healthloop.com", "password": "demo123", "role": "client", "points": 650, "level": "Active"},
            {"email": "nutricionista@healthloop.com", "password": "demo123", "role": "nutritionist", "points": 300, "level": "Active"},
            {"email": "entrenador@healthloop.com", "password": "demo123", "role": "trainer", "points": 150, "level": "Beginner"}
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

# Video Gallery Routes
@app.get("/api/videos")
async def get_videos():
    """Get all available videos"""
    demo_videos = [
        {
            "id": "video-1",
            "title": "Rutina Cardio Intenso 20min",
            "description": "Quema grasa y mejora tu resistencia con esta rutina de cardio de alta intensidad.",
            "category": "Cardio",
            "youtube_id": "dQw4w9WgXcQ",
            "duration": 20,
            "points": 50,
            "difficulty": "Intermedio",
            "equipment": "Sin equipo",
            "instructor": "Carlos Fitness"
        },
        {
            "id": "video-2", 
            "title": "Yoga para Principiantes",
            "description": "Sesión relajante de yoga perfecta para comenzar tu práctica de mindfulness.",
            "category": "Yoga",
            "youtube_id": "dQw4w9WgXcQ",
            "duration": 30,
            "points": 50,
            "difficulty": "Principiante",
            "equipment": "Mat de yoga",
            "instructor": "Ana Wellness"
        },
        {
            "id": "video-3",
            "title": "Fuerza Total Body",
            "description": "Entrena todo tu cuerpo con ejercicios de fuerza usando peso corporal.",
            "category": "Fuerza",
            "youtube_id": "dQw4w9WgXcQ",
            "duration": 25,
            "points": 50,
            "difficulty": "Intermedio",
            "equipment": "Sin equipo",
            "instructor": "Miguel Strong"
        },
        {
            "id": "video-4",
            "title": "Nutrición Saludable Básica",
            "description": "Aprende los fundamentos de una alimentación equilibrada y nutritiva.",
            "category": "Nutrición",
            "youtube_id": "dQw4w9WgXcQ",
            "duration": 15,
            "points": 50,
            "difficulty": "Principiante", 
            "equipment": "Ninguno",
            "instructor": "Dr. María López"
        }
    ]
    return demo_videos

@app.post("/api/videos/{video_id}/complete")
async def complete_video(video_id: str, current_user: User = Depends(get_current_user)):
    """Mark video as completed and award points"""
    try:
        # Award 50 points for video completion using existing award_points function
        points_awarded = await award_points(current_user.id, PointAction.VIDEO_COMPLETION, "Video completado exitosamente")
        
        return {
            "message": "Video completado exitosamente",
            "points_awarded": points_awarded
        }
    except Exception as e:
        logger.error(f"Error completing video: {e}")
        raise HTTPException(status_code=500, detail="Error al completar video")

# Cart Management Routes
@app.get("/api/cart")
async def get_cart(current_user: User = Depends(get_current_user)):
    """Get user's current cart"""
    try:
        cart = await db.carts.find_one({"user_id": current_user.id})
        if not cart:
            # Create empty cart if doesn't exist
            new_cart = {
                "id": str(uuid.uuid4()),
                "user_id": current_user.id,
                "items": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.carts.insert_one(new_cart)
            return {"items": [], "total": 0.0}
        
        # Calculate cart total
        total = 0.0
        cart_items = []
        
        for item in cart.get("items", []):
            product = await db.products.find_one({"id": item["product_id"]})
            if product:
                item_total = product["price"] * item["quantity"]
                total += item_total
                cart_items.append({
                    "product_id": item["product_id"],
                    "product_name": product["name"],
                    "product_price": product["price"],
                    "quantity": item["quantity"],
                    "item_total": item_total,
                    "image_url": product.get("image_url", "")
                })
        
        return {
            "items": cart_items,
            "total": round(total, 2)
        }
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener carrito")

@app.post("/api/cart/add")
async def add_to_cart(request: CartAddRequest, current_user: User = Depends(get_current_user)):
    """Add product to cart"""
    try:
        # Verify product exists
        product = await db.products.find_one({"id": request.product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Get or create cart
        cart = await db.carts.find_one({"user_id": current_user.id})
        if not cart:
            cart = {
                "id": str(uuid.uuid4()),
                "user_id": current_user.id,
                "items": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.carts.insert_one(cart)
        
        # Check if product already in cart
        items = cart.get("items", [])
        existing_item = None
        for item in items:
            if item["product_id"] == request.product_id:
                existing_item = item
                break
        
        if existing_item:
            # Update quantity
            existing_item["quantity"] += request.quantity
        else:
            # Add new item
            items.append({
                "product_id": request.product_id,
                "quantity": request.quantity
            })
        
        # Update cart
        await db.carts.update_one(
            {"user_id": current_user.id},
            {
                "$set": {
                    "items": items,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {"message": "Producto agregado al carrito exitosamente"}
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail="Error al agregar producto al carrito")

@app.delete("/api/cart/clear")
async def clear_cart(current_user: User = Depends(get_current_user)):
    """Clear user's cart"""
    try:
        await db.carts.update_one(
            {"user_id": current_user.id},
            {
                "$set": {
                    "items": [],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        return {"message": "Carrito vaciado exitosamente"}
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail="Error al vaciar carrito")

@app.post("/api/orders")
async def create_order(current_user: User = Depends(get_current_user)):
    """Create order from cart and award points"""
    try:
        # Get cart
        cart = await db.carts.find_one({"user_id": current_user.id})
        if not cart or not cart.get("items"):
            raise HTTPException(status_code=400, detail="Carrito vacío")
        
        # Calculate total
        total = 0.0
        for item in cart["items"]:
            product = await db.products.find_one({"id": item["product_id"]})
            if product:
                total += product["price"] * item["quantity"]
        
        # Create order
        order = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "items": cart["items"],
            "total_amount": round(total, 2),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.orders.insert_one(order)
        
        # Award points for purchase (10 points per dollar)
        points_earned = int(total * 10)
        await award_points(current_user.id, PointAction.PURCHASE, f"Compra por ${total:.2f}", points_earned)
        
        # Clear cart
        await db.carts.update_one(
            {"user_id": current_user.id},
            {"$set": {"items": [], "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {
            "message": "Pedido creado exitosamente",
            "order_id": order["id"],
            "total": total,
            "points_earned": points_earned
        }
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Error al crear pedido")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()