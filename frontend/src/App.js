import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { ShoppingCart, Plus, Minus, Check, Star, Leaf, Heart, Zap, ShoppingBag } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Landing Page Component
const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      {/* Header */}
      <nav className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-green-500 rounded-full flex items-center justify-center">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                HealthLoop Nexus
              </span>
            </div>
            <Button 
              onClick={() => navigate('/marketplace')}
              className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-medium px-6 py-2 rounded-full transition-all duration-300 transform hover:scale-105"
              data-testid="explore-marketplace-btn"
            >
              <ShoppingBag className="w-4 h-4 mr-2" />
              Explorar Marketplace
            </Button>
          </div>
        </div>
      </nav>

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
                onClick={() => navigate('/marketplace')}
                className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-semibold px-8 py-4 rounded-full text-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
                data-testid="get-started-btn"
              >
                <Zap className="w-5 h-5 mr-2" />
                Comenzar Ahora
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="border-2 border-blue-200 text-blue-700 hover:bg-blue-50 font-semibold px-8 py-4 rounded-full text-lg transition-all duration-300"
                data-testid="learn-more-btn"
              >
                Conocer Más
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

// Marketplace Component
const Marketplace = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [selectedDietType, setSelectedDietType] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    initializeData();
    fetchProducts();
    fetchCart();
  }, []);

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
    try {
      const response = await axios.get(`${API}/cart`);
      setCart(response.data);
    } catch (error) {
      console.error('Error fetching cart:', error);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
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
      {/* Header */}
      <nav className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50">
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
            <Button 
              onClick={() => navigate('/cart')}
              variant="outline"
              className="border-2 border-blue-200 text-blue-700 hover:bg-blue-50"
              data-testid="cart-button"
            >
              <ShoppingCart className="w-4 h-4 mr-2" />
              Carrito ({cart.items.length})
            </Button>
          </div>
        </div>
      </nav>

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

// Cart Component
const Cart = () => {
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [showCheckout, setShowCheckout] = useState(false);
  const [userInfo, setUserInfo] = useState({ email: '', name: '' });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCart();
  }, []);

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
    if (!userInfo.email || !userInfo.name) {
      toast.error('Por favor completa todos los campos');
      return;
    }

    try {
      const response = await axios.post(`${API}/orders`, {
        user_email: userInfo.email,
        user_name: userInfo.name
      });

      toast.success('¡Pago procesado exitosamente (Demo)!');
      
      // Redirect to success page after a short delay
      setTimeout(() => {
        navigate('/success', { 
          state: { 
            order: response.data,
            userInfo: userInfo
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
      {/* Header */}
      <nav className="bg-white/80 backdrop-blur-md shadow-sm">
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
            <Button 
              onClick={() => navigate('/marketplace')}
              variant="outline"
              className="border-2 border-blue-200 text-blue-700 hover:bg-blue-50"
            >
              Volver al Marketplace
            </Button>
          </div>
        </div>
      </nav>

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
                  <CardTitle className="text-xl">Información de Checkout (Demo)</CardTitle>
                  <CardDescription>
                    Completa tus datos para finalizar la compra
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4" data-testid="checkout-form">
                  <div>
                    <Label htmlFor="name">Nombre Completo</Label>
                    <Input
                      id="name"
                      value={userInfo.name}
                      onChange={(e) => setUserInfo({...userInfo, name: e.target.value})}
                      placeholder="Tu nombre completo"
                      data-testid="checkout-name-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={userInfo.email}
                      onChange={(e) => setUserInfo({...userInfo, email: e.target.value})}
                      placeholder="tu@email.com"
                      data-testid="checkout-email-input"
                    />
                  </div>
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

// Success Page Component
const SuccessPage = () => {
  const navigate = useNavigate();
  const [orderData, setOrderData] = useState(null);

  useEffect(() => {
    // In a real app, this would come from route state or props
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
            Tu pedido ha sido procesado exitosamente en modo demo.
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
              onClick={() => navigate('/marketplace')}
              className="w-full bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white"
              data-testid="continue-shopping-success-btn"
            >
              Continuar Comprando
            </Button>
            <Button
              onClick={() => navigate('/')}
              variant="outline"
              className="w-full border-2 border-gray-200 text-gray-700 hover:bg-gray-50"
              data-testid="back-home-btn"
            >
              Volver al Inicio
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
    <div className="App">
      <Toaster position="top-right" />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/marketplace" element={<Marketplace />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/success" element={<SuccessPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;