import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { 
  ShoppingCart, Plus, Check, Star, Leaf, Heart, Zap, ShoppingBag, 
  User, LogOut, Calendar, TrendingUp, Users, DollarSign, 
  Award, Target, Clock, ChevronRight
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        const response = await axios.get(`${API}/auth/me`);
        setUser(response.data);
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      }
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      toast.success(`¡Bienvenido, ${userData.name}!`);
      return userData;
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Error al iniciar sesión');
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { access_token, user: newUser } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(newUser);
      
      toast.success(`¡Cuenta creada exitosamente! Bienvenido, ${newUser.name}!`);
      return newUser;
    } catch (error) {
      console.error('Register error:', error);
      toast.error('Error al crear cuenta');
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.success('Sesión cerrada exitosamente');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Navigation Header Component
const NavigationHeader = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="bg-white/90 backdrop-blur-md shadow-sm sticky top-0 z-50 border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-green-500 rounded-full flex items-center justify-center">
              <Heart className="w-6 h-6 text-white" />
            </div>
            <span 
              onClick={() => navigate('/')}
              className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent cursor-pointer"
            >
              HealthLoop Nexus
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Button
                  variant="ghost"
                  onClick={() => navigate('/marketplace')}
                  className="text-gray-600 hover:text-blue-600"
                >
                  <ShoppingBag className="w-4 h-4 mr-2" />
                  Marketplace
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => navigate('/dashboard')}
                  className="text-gray-600 hover:text-blue-600"
                >
                  <User className="w-4 h-4 mr-2" />
                  Dashboard
                </Button>
                <div className="flex items-center space-x-2 bg-gradient-to-r from-yellow-100 to-yellow-50 px-3 py-1 rounded-full">
                  <Award className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-700">{user.points} pts</span>
                </div>
                <Button
                  variant="outline"
                  onClick={logout}
                  className="border-red-200 text-red-600 hover:bg-red-50"
                  data-testid="logout-btn"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Salir
                </Button>
              </>
            ) : (
              <Button 
                onClick={() => navigate('/auth')}
                className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-medium px-6 py-2 rounded-full"
                data-testid="login-btn"
              >
                Iniciar Sesión
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Landing Page Component
const LandingPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      <NavigationHeader />

      {/* Hero Section */}
      <div className="relative overflow-hidden py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Tu Ecosistema de 
              <span className="bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent block">
                Wellness Completo
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Conectamos nutricionistas, entrenadores y comidas saludables en una sola plataforma. 
              Transforma tu estilo de vida con productos premium y servicios profesionales.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Button 
                size="lg" 
                onClick={() => navigate(user ? '/dashboard' : '/auth')}
                className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-semibold px-8 py-4 rounded-full text-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
                data-testid="get-started-btn"
              >
                <Zap className="w-5 h-5 mr-2" />
                {user ? 'Ir al Dashboard' : 'Comenzar Ahora'}
              </Button>
              <Button 
                size="lg" 
                onClick={() => navigate('/marketplace')}
                variant="outline" 
                className="border-2 border-blue-200 text-blue-700 hover:bg-blue-50 font-semibold px-8 py-4 rounded-full text-lg transition-all duration-300"
                data-testid="explore-marketplace-btn"
              >
                <ShoppingBag className="w-5 h-5 mr-2" />
                Explorar Marketplace
              </Button>
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-3 gap-8 mt-16">
              <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Leaf className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">Comidas Saludables</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Catálogo de comidas premium: Keto, Mediterráneo, Vegano. $12-25 por comida.
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Star className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">Profesionales</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Nutricionistas y entrenadores certificados. Consultas de 30min por $30.
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">Recompensas</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Gana HealthLoop Points y canjea por descuentos y productos exclusivos.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Auth Page Component
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'client',
    professional_type: '',
    specialization: ''
  });
  
  const navigate = useNavigate();
  const { login, register, user } = useAuth();

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (isLogin) {
        const userData = await login(formData.email, formData.password);
        navigate('/dashboard');
      } else {
        const userData = await register(formData);
        navigate('/dashboard');
      }
    } catch (error) {
      // Error handling is done in the auth context
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = (type) => {
    const demoCredentials = {
      client: { email: 'cliente@healthloop.com', password: 'demo123' },
      nutritionist: { email: 'nutricionista@healthloop.com', password: 'demo123' },
      trainer: { email: 'entrenador@healthloop.com', password: 'demo123' }
    };
    
    setFormData({
      ...formData,
      email: demoCredentials[type].email,
      password: demoCredentials[type].password
    });
    setIsLogin(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      <NavigationHeader />
      
      <div className="flex items-center justify-center py-12">
        <Card className="w-full max-w-md bg-white/90 backdrop-blur-sm shadow-xl border-0">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-gray-900">
              {isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}
            </CardTitle>
            <CardDescription>
              {isLogin ? 'Accede a tu dashboard personalizado' : 'Únete al ecosistema HealthLoop Nexus'}
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {/* Demo Credentials */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-blue-800 mb-2">Cuentas Demo:</p>
              <div className="space-y-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => fillDemoCredentials('client')}
                  data-testid="demo-client-btn"
                >
                  👤 Cliente Demo
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => fillDemoCredentials('nutritionist')}
                  data-testid="demo-nutritionist-btn"
                >
                  🥗 Nutricionista Demo
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => fillDemoCredentials('trainer')}
                  data-testid="demo-trainer-btn"
                >
                  💪 Entrenador Demo
                </Button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4" data-testid="auth-form">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                  data-testid="email-input"
                />
              </div>
              
              <div>
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  data-testid="password-input"
                />
              </div>

              {!isLogin && (
                <>
                  <div>
                    <Label htmlFor="name">Nombre Completo</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      required
                      data-testid="name-input"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="role">Tipo de Cuenta</Label>
                    <Select value={formData.role} onValueChange={(value) => setFormData({...formData, role: value})}>
                      <SelectTrigger data-testid="role-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="client">Cliente</SelectItem>
                        <SelectItem value="professional">Profesional</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.role === 'professional' && (
                    <>
                      <div>
                        <Label htmlFor="professional_type">Tipo de Profesional</Label>
                        <Select value={formData.professional_type} onValueChange={(value) => setFormData({...formData, professional_type: value})}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="nutritionist">Nutricionista</SelectItem>
                            <SelectItem value="trainer">Entrenador</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div>
                        <Label htmlFor="specialization">Especialización</Label>
                        <Input
                          id="specialization"
                          value={formData.specialization}
                          onChange={(e) => setFormData({...formData, specialization: e.target.value})}
                          placeholder="ej: Nutrición Deportiva, Entrenamiento Funcional"
                        />
                      </div>
                    </>
                  )}
                </>
              )}

              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700"
                disabled={loading}
                data-testid="auth-submit-btn"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                ) : null}
                {isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}
              </Button>
            </form>
          </CardContent>
          
          <CardFooter className="text-center">
            <Button
              variant="ghost"
              onClick={() => setIsLogin(!isLogin)}
              className="w-full text-blue-600"
              data-testid="toggle-auth-mode-btn"
            >
              {isLogin ? '¿No tienes cuenta? Registrarse' : '¿Ya tienes cuenta? Iniciar sesión'}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

// Client Dashboard Component
const ClientDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/client`);
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Error al cargar dashboard');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      <NavigationHeader />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2" data-testid="welcome-message">
            ¡Bienvenido, {dashboardData?.user.name}! 👋
          </h1>
          <p className="text-lg text-gray-600">
            Aquí tienes un resumen de tu progreso wellness
          </p>
        </div>

        {/* Points and Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-white border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-yellow-100 text-sm">Tus Puntos</p>
                  <p className="text-2xl font-bold" data-testid="user-points">{dashboardData?.user.points} pts</p>
                </div>
                <Award className="w-8 h-8 text-yellow-100" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Próximas Consultas</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData?.upcoming_appointments.length}</p>
                </div>
                <Calendar className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Órdenes Recientes</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData?.recent_orders.length}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upcoming Appointments */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center text-xl text-gray-900">
                <Calendar className="w-5 h-5 mr-2 text-blue-500" />
                Tus Próximas Consultas
              </CardTitle>
            </CardHeader>
            <CardContent data-testid="upcoming-appointments">
              {dashboardData?.upcoming_appointments.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.upcoming_appointments.map((appointment, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                      <div>
                        <p className="font-semibold text-gray-900">{appointment.professional_name}</p>
                        <p className="text-sm text-gray-600">{appointment.professional_type}</p>
                        <p className="text-xs text-blue-600">
                          {new Date(appointment.date).toLocaleDateString('es-ES', { 
                            weekday: 'long', 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                      <Badge variant="outline" className="bg-green-100 text-green-800">
                        {appointment.duration} min
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Calendar className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>Sin consultas programadas</p>
                  <Button 
                    className="mt-3 bg-blue-600 hover:bg-blue-700 text-white"
                    size="sm"
                  >
                    Agendar Consulta
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recommended Products */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-xl text-gray-900">
                <div className="flex items-center">
                  <Star className="w-5 h-5 mr-2 text-yellow-500" />
                  Productos Recomendados
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/marketplace')}
                  className="text-blue-600 hover:text-blue-800"
                  data-testid="view-all-products-btn"
                >
                  Ver Todos <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent data-testid="recommended-products">
              <div className="space-y-4">
                {dashboardData?.recommended_products.slice(0, 3).map((product) => (
                  <div key={product.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <img 
                      src={product.image_url} 
                      alt={product.name}
                      className="w-16 h-16 object-cover rounded-lg"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{product.name}</p>
                      <p className="text-sm text-gray-600">{product.calories} cal</p>
                      <p className="text-lg font-bold text-green-600">${product.price}</p>
                    </div>
                    <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
              
              <Button
                onClick={() => navigate('/marketplace')}
                className="w-full mt-4 bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white"
                data-testid="continue-shopping-btn"
              >
                <ShoppingBag className="w-4 h-4 mr-2" />
                Seguir Comprando
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Professional Dashboard Component  
const ProfessionalDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/professional`);
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Error al cargar dashboard');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      <NavigationHeader />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2" data-testid="professional-welcome">
            Panel de {dashboardData?.professional_info.type === 'nutritionist' ? 'Nutricionista' : 'Entrenador'} 👩‍⚕️
          </h1>
          <p className="text-lg text-gray-600">
            Gestiona tus clientes y consultas - {dashboardData?.user.name}
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Clientes Activos</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData?.assigned_clients.length}</p>
                </div>
                <Users className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Próximas Consultas</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData?.upcoming_appointments.length}</p>
                </div>
                <Calendar className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-r from-green-400 to-green-500 text-white border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm">Comisiones Pendientes</p>
                  <p className="text-2xl font-bold" data-testid="commission-amount">${dashboardData?.commission_pending}</p>
                </div>
                <DollarSign className="w-8 h-8 text-green-100" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Tarifa por Hora</p>
                  <p className="text-2xl font-bold text-gray-900">${dashboardData?.professional_info.hourly_rate}</p>
                </div>
                <Clock className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Assigned Clients */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center text-xl text-gray-900">
                <Users className="w-5 h-5 mr-2 text-blue-500" />
                Tus Clientes Asignados
              </CardTitle>
            </CardHeader>
            <CardContent data-testid="assigned-clients">
              <div className="space-y-4">
                {dashboardData?.assigned_clients.map((client) => (
                  <div key={client.id} className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{client.name}</p>
                        <p className="text-sm text-gray-600">
                          <Target className="w-3 h-3 inline mr-1" />
                          {client.objective}
                        </p>
                        <p className="text-xs text-gray-500">Desde: {client.start_date}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className="bg-green-100 text-green-800">
                      {client.progress}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Upcoming Appointments */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center text-xl text-gray-900">
                <Calendar className="w-5 h-5 mr-2 text-green-500" />
                Próximas Consultas
              </CardTitle>
            </CardHeader>
            <CardContent data-testid="professional-appointments">
              <div className="space-y-4">
                {dashboardData?.upcoming_appointments.map((appointment) => (
                  <div key={appointment.id} className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                    <div>
                      <p className="font-semibold text-gray-900">{appointment.client_name}</p>
                      <p className="text-sm text-gray-600">{appointment.type}</p>
                      <p className="text-xs text-green-600">
                        {new Date(appointment.date).toLocaleDateString('es-ES', { 
                          weekday: 'short',
                          day: 'numeric',
                          month: 'short',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline" className="bg-blue-100 text-blue-800 mb-2">
                        {appointment.duration} min
                      </Badge>
                      <Button size="sm" className="block bg-green-600 hover:bg-green-700 text-white">
                        Unirse
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Dashboard Router Component
const Dashboard = () => {
  const { user } = useAuth();
  
  if (user?.role === 'client') {
    return <ClientDashboard />;
  } else if (user?.role === 'professional') {
    return <ProfessionalDashboard />;
  } else {
    return <Navigate to="/auth" replace />;
  }
};

// Marketplace Component (Updated to work with auth)
const Marketplace = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [selectedDietType, setSelectedDietType] = useState('');
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    initializeData();
    fetchProducts();
    if (user) {
      fetchCart();
    }
  }, [user]);

  const initializeData = async () => {
    try {
      await axios.post(`${API}/init-demo-data`);
    } catch (error) {
      console.error('Error initializing demo data:', error);
    }
  };

  const fetchProducts = async (dietType = '') => {
    try {
      const url = dietType ? `${API}/products?diet_type=${dietType}` : `${API}/products`;
      const response = await axios.get(url);
      setProducts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Error al cargar productos');
      setLoading(false);
    }
  };

  const fetchCart = async () => {
    if (!user) return;
    try {
      const response = await axios.get(`${API}/cart`);
      setCart(response.data);
    } catch (error) {
      console.error('Error fetching cart:', error);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    if (!user) {
      toast.error('Debes iniciar sesión para agregar productos al carrito');
      navigate('/auth');
      return;
    }

    try {
      await axios.post(`${API}/cart/add`, {
        product_id: productId,
        quantity: quantity
      });
      fetchCart();
      toast.success('Producto agregado al carrito');
    } catch (error) {
      console.error('Error adding to cart:', error);
      toast.error('Error al agregar al carrito');
    }
  };

  const handleDietFilter = (dietType) => {
    setSelectedDietType(dietType);
    fetchProducts(dietType);
  };

  const getDietTypeColor = (dietType) => {
    switch (dietType) {
      case 'keto': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'mediterranean': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'vegan': return 'bg-green-100 text-green-800 border-green-200';
      case 'healthy': return 'bg-purple-100 text-purple-800 border-purple-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getDietTypeIcon = (dietType) => {
    switch (dietType) {
      case 'keto': return '🥑';
      case 'mediterranean': return '🫒';
      case 'vegan': return '🌱';
      case 'healthy': return '✨';
      default: return '🍽️';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Cargando productos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      <NavigationHeader />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Marketplace de Comidas Saludables</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Descubre nuestro catálogo premium de comidas nutritivas y sabrosas, 
            diseñadas por expertos en nutrición.
          </p>
        </div>

        {/* Diet Type Filters */}
        <div className="flex flex-wrap gap-3 justify-center mb-8" data-testid="diet-filters">
          <Button
            onClick={() => handleDietFilter('')}
            variant={selectedDietType === '' ? 'default' : 'outline'}
            className="rounded-full"
            data-testid="filter-all"
          >
            Todos
          </Button>
          <Button
            onClick={() => handleDietFilter('healthy')}
            variant={selectedDietType === 'healthy' ? 'default' : 'outline'}
            className="rounded-full"
            data-testid="filter-healthy"
          >
            ✨ Saludable
          </Button>
          <Button
            onClick={() => handleDietFilter('keto')}
            variant={selectedDietType === 'keto' ? 'default' : 'outline'}
            className="rounded-full"
            data-testid="filter-keto"
          >
            🥑 Keto
          </Button>
          <Button
            onClick={() => handleDietFilter('mediterranean')}
            variant={selectedDietType === 'mediterranean' ? 'default' : 'outline'}
            className="rounded-full"
            data-testid="filter-mediterranean"
          >
            🫒 Mediterráneo
          </Button>
          <Button
            onClick={() => handleDietFilter('vegan')}
            variant={selectedDietType === 'vegan' ? 'default' : 'outline'}
            className="rounded-full"
            data-testid="filter-vegan"
          >
            🌱 Vegano
          </Button>
        </div>

        {/* Products Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="products-grid">
          {products.map((product) => (
            <Card key={product.id} className="bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 overflow-hidden">
              <div className="relative">
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-48 object-cover"
                />
                <Badge className={`absolute top-3 right-3 ${getDietTypeColor(product.diet_type)}`}>
                  {getDietTypeIcon(product.diet_type)} {product.diet_type}
                </Badge>
              </div>
              <CardHeader>
                <CardTitle className="text-xl text-gray-900">{product.name}</CardTitle>
                <CardDescription className="text-gray-600">
                  {product.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-2xl font-bold text-green-600">${product.price}</span>
                  <Badge variant="outline" className="text-sm">
                    {product.calories} cal
                  </Badge>
                </div>
                <div className="text-sm text-gray-600">
                  <strong>Ingredientes:</strong> {product.ingredients.slice(0, 3).join(', ')}
                  {product.ingredients.length > 3 && '...'}
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  onClick={() => addToCart(product.id)}
                  className="w-full bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-medium rounded-full transition-all duration-300"
                  data-testid={`add-to-cart-${product.id}`}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Agregar al Carrito
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

// Cart Component (Updated with auth)
const Cart = () => {
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [showCheckout, setShowCheckout] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchCart();
    } else {
      navigate('/auth');
    }
  }, [user, navigate]);

  const fetchCart = async () => {
    try {
      const response = await axios.get(`${API}/cart`);
      setCart(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching cart:', error);
      setLoading(false);
    }
  };

  const clearCart = async () => {
    try {
      await axios.delete(`${API}/cart/clear`);
      setCart({ items: [], total: 0 });
      toast.success('Carrito vaciado');
    } catch (error) {
      console.error('Error clearing cart:', error);
      toast.error('Error al vaciar carrito');
    }
  };

  const processOrder = async () => {
    try {
      const response = await axios.post(`${API}/orders`);
      toast.success('¡Pago procesado exitosamente (Demo)!');
      
      setTimeout(() => {
        navigate('/success', { 
          state: { 
            order: response.data,
            userInfo: user
          } 
        });
      }, 1500);

    } catch (error) {
      console.error('Error processing order:', error);
      toast.error('Error al procesar la orden');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Cargando carrito...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      <NavigationHeader />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Mi Carrito</h1>

        {cart.items.length === 0 ? (
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg text-center p-8">
            <div className="text-gray-500 text-lg">
              <ShoppingCart className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              Tu carrito está vacío
            </div>
            <Button 
              onClick={() => navigate('/marketplace')}
              className="mt-4 bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white"
              data-testid="continue-shopping-btn"
            >
              Continuar Comprando
            </Button>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Cart Items */}
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-xl">Productos en tu carrito</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4" data-testid="cart-items">
                {cart.items.map((item, index) => (
                  <div key={index} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                    <img
                      src={item.product.image_url}
                      alt={item.product.name}
                      className="w-16 h-16 object-cover rounded-lg"
                    />
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{item.product.name}</h3>
                      <p className="text-sm text-gray-600">Cantidad: {item.quantity}</p>
                      <p className="text-sm text-green-600 font-medium">${item.product.price} c/u</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900">${item.subtotal}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
              <Separator />
              <CardFooter className="flex justify-between items-center">
                <Button
                  variant="destructive"
                  onClick={clearCart}
                  data-testid="clear-cart-btn"
                >
                  Vaciar Carrito
                </Button>
                <div className="text-2xl font-bold text-green-600" data-testid="cart-total">
                  Total: ${cart.total}
                </div>
              </CardFooter>
            </Card>

            {/* Checkout Section */}
            {!showCheckout ? (
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <Button
                    onClick={() => setShowCheckout(true)}
                    className="w-full bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-semibold py-4 rounded-full text-lg"
                    data-testid="proceed-checkout-btn"
                  >
                    <Check className="w-5 h-5 mr-2" />
                    Proceder al Checkout
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="text-xl">Confirmar Pedido (Demo)</CardTitle>
                  <CardDescription>
                    Usuario: {user?.name} ({user?.email})
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4" data-testid="checkout-form">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-sm text-yellow-800">
                      <strong>🎭 Modo Demo:</strong> Esta es una compra simulada. 
                      No se procesarán pagos reales.
                    </p>
                  </div>
                </CardContent>
                <CardFooter className="space-x-4">
                  <Button
                    variant="outline"
                    onClick={() => setShowCheckout(false)}
                    data-testid="back-to-cart-btn"
                  >
                    Volver
                  </Button>
                  <Button
                    onClick={processOrder}
                    className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white"
                    data-testid="confirm-order-btn"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Confirmar Pedido (Demo)
                  </Button>
                </CardFooter>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Success Page Component (Updated)
const SuccessPage = () => {
  const navigate = useNavigate();
  const [orderData, setOrderData] = useState(null);

  useEffect(() => {
    setOrderData({
      id: 'DEMO-' + Math.random().toString(36).substr(2, 9),
      total: 45.50,
      status: 'completed'
    });
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100 flex items-center justify-center">
      <Card className="bg-white/90 backdrop-blur-sm border-0 shadow-2xl max-w-md w-full mx-4">
        <CardContent className="p-8 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-2xl font-bold text-gray-900 mb-4" data-testid="success-title">
            ¡Pedido Confirmado!
          </h1>
          
          <p className="text-gray-600 mb-6">
            Tu pedido ha sido procesado exitosamente en modo demo. ¡Has ganado puntos adicionales!
          </p>
          
          {orderData && (
            <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
              <p className="text-sm text-gray-600">
                <strong>Número de Orden:</strong> {orderData.id}
              </p>
              <p className="text-sm text-gray-600">
                <strong>Estado:</strong> Completado (Demo)
              </p>
              <p className="text-sm text-gray-600">
                <strong>Total:</strong> ${orderData.total}
              </p>
            </div>
          )}
          
          <div className="space-y-3">
            <Button
              onClick={() => navigate('/dashboard')}
              className="w-full bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white"
              data-testid="back-dashboard-btn"
            >
              <User className="w-4 h-4 mr-2" />
              Volver al Dashboard
            </Button>
            <Button
              onClick={() => navigate('/marketplace')}
              variant="outline"
              className="w-full border-2 border-gray-200 text-gray-700 hover:bg-gray-50"
              data-testid="continue-shopping-success-btn"
            >
              Continuar Comprando
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <Toaster position="top-right" />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/marketplace" element={<Marketplace />} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/cart" element={<ProtectedRoute><Cart /></ProtectedRoute>} />
            <Route path="/success" element={<ProtectedRoute><SuccessPage /></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;