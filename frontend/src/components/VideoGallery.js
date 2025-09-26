import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Video, PlayCircle, CheckCircle, Search, Heart, ShoppingBag, 
  User, Award, LogOut
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Demo Videos Data
const demoVideos = [
  {
    id: 'video-1',
    title: 'Rutina Cardio Intenso 20min',
    description: 'Quema grasa y mejora tu resistencia con esta rutina de cardio de alta intensidad.',
    category: 'Cardio',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 20,
    points: 50,
    difficulty: 'Intermedio',
    equipment: 'Sin equipo',
    instructor: 'Carlos Fitness'
  },
  {
    id: 'video-2',
    title: 'Yoga para Principiantes',
    description: 'Sesión relajante de yoga perfecta para comenzar tu práctica de mindfulness.',
    category: 'Yoga',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 30,
    points: 50,
    difficulty: 'Principiante',
    equipment: 'Mat de yoga',
    instructor: 'Ana Wellness'
  },
  {
    id: 'video-3',
    title: 'Fuerza Total Body',
    description: 'Entrena todo tu cuerpo con ejercicios de fuerza usando peso corporal.',
    category: 'Fuerza',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 25,
    points: 50,
    difficulty: 'Avanzado',
    equipment: 'Pesas opcionales',
    instructor: 'Carlos Fitness'
  },
  {
    id: 'video-4',
    title: 'Nutrición: Preparación de Batidos',
    description: 'Aprende a preparar batidos nutritivos y deliciosos para tu día a día.',
    category: 'Nutrición',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 15,
    points: 50,
    difficulty: 'Principiante',
    equipment: 'Licuadora',
    instructor: 'Dr. María López'
  },
  {
    id: 'video-5',
    title: 'HIIT Avanzado 15min',
    description: 'Rutina de intervalos de alta intensidad para máximos resultados en poco tiempo.',
    category: 'Cardio',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 15,
    points: 50,
    difficulty: 'Avanzado',
    equipment: 'Sin equipo',
    instructor: 'Carlos Fitness'
  },
  {
    id: 'video-6',
    title: 'Yoga Restaurativo',
    description: 'Relaja tu cuerpo y mente con posturas suaves y respiración consciente.',
    category: 'Yoga',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 35,
    points: 50,
    difficulty: 'Principiante',
    equipment: 'Mat de yoga, cojines',
    instructor: 'Ana Wellness'
  },
  {
    id: 'video-7',
    title: 'Fuerza de Brazos y Hombros',
    description: 'Fortalece la parte superior de tu cuerpo con ejercicios específicos.',
    category: 'Fuerza',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 20,
    points: 50,
    difficulty: 'Intermedio',
    equipment: 'Pesas o botellas',
    instructor: 'Carlos Fitness'
  },
  {
    id: 'video-8',
    title: 'Planificación de Comidas Saludables',
    description: 'Guía práctica para planificar y preparar comidas nutritivas para la semana.',
    category: 'Nutrición',
    youtubeId: 'dQw4w9WgXcQ',
    duration: 25,
    points: 50,
    difficulty: 'Principiante',
    equipment: 'Ninguno',
    instructor: 'Dr. María López'
  }
];

// Video Gallery Component
const VideoGallery = ({ user, updateUserPoints }) => {
  const [filteredVideos, setFilteredVideos] = useState(demoVideos);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [completedVideos, setCompletedVideos] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      const completed = JSON.parse(localStorage.getItem(`completed_videos_${user.id}`) || '[]');
      setCompletedVideos(completed);
    }
  }, [user]);

  useEffect(() => {
    filterVideos();
  }, [selectedCategory, searchTerm]);

  const filterVideos = () => {
    let filtered = demoVideos;
    
    if (selectedCategory) {
      filtered = filtered.filter(video => video.category === selectedCategory);
    }
    
    if (searchTerm) {
      filtered = filtered.filter(video =>
        video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        video.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    setFilteredVideos(filtered);
  };

  const completeVideo = async (videoId) => {
    if (!user) return;

    const updatedCompleted = [...completedVideos, videoId];
    setCompletedVideos(updatedCompleted);
    localStorage.setItem(`completed_videos_${user.id}`, JSON.stringify(updatedCompleted));

    // Award points for completing video
    try {
      await axios.post(`${API}/points/add`, {
        action: 'complete_consultation', // Using existing action for demo
        description: 'Video completado'
      });

      // Update user points in context
      const updatedUser = await axios.get(`${API}/auth/me`);
      updateUserPoints(
        updatedUser.data.points, 
        updatedUser.data.total_points_earned, 
        updatedUser.data.level
      );

      toast.success('¡Video completado! +50 puntos ganados');
    } catch (error) {
      console.error('Error awarding points:', error);
      toast.error('Error al otorgar puntos');
    }
  };

  const categories = ['Cardio', 'Fuerza', 'Yoga', 'Nutrición'];

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'Principiante': return 'bg-green-100 text-green-800';
      case 'Intermedio': return 'bg-yellow-100 text-yellow-800';
      case 'Avanzado': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Cardio': return '💓';
      case 'Fuerza': return '💪';
      case 'Yoga': return '🧘';
      case 'Nutrición': return '🥗';
      default: return '📹';
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100 flex items-center justify-center">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-8 text-center">
            <Video className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h2 className="text-2xl font-bold mb-4">Acceso Requerido</h2>
            <p className="text-gray-600 mb-6">Inicia sesión para acceder a nuestra biblioteca de videos premium</p>
            <Button onClick={() => navigate('/auth')} className="bg-blue-600 hover:bg-blue-700">
              Iniciar Sesión
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-blue-100">
      {/* Header */}
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
              
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1 bg-gradient-to-r from-yellow-100 to-yellow-50 px-3 py-1 rounded-full">
                  <Award className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-700" data-testid="header-points">
                    {user.points} pts
                  </span>
                </div>
                <Badge className={user.level === 'Active' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}>
                  {user.level}
                </Badge>
              </div>
              
              <Button
                variant="outline"
                onClick={() => {
                  localStorage.removeItem('token');
                  delete axios.defaults.headers.common['Authorization'];
                  navigate('/auth');
                }}
                className="border-red-200 text-red-600 hover:bg-red-50"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Salir
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Videos On-Demand</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Accede a nuestra biblioteca premium de entrenamientos y contenido wellness. 
            ¡Gana puntos completando videos!
          </p>
        </div>

        {/* Video Progress Stats */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg mb-8">
          <CardContent className="p-6">
            <div className="grid md:grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-3xl font-bold text-purple-600">{completedVideos.length}</div>
                <div className="text-sm text-gray-600">Videos Completados</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600">{completedVideos.length * 50}</div>
                <div className="text-sm text-gray-600">Puntos de Videos</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-600">{Math.round((completedVideos.length / demoVideos.length) * 100)}%</div>
                <div className="text-sm text-gray-600">Progreso Total</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Filters and Search */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg mb-8">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Buscar videos..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                    data-testid="video-search"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={selectedCategory === '' ? 'default' : 'outline'}
                  onClick={() => setSelectedCategory('')}
                  className="rounded-full"
                  data-testid="filter-all-videos"
                >
                  Todos
                </Button>
                {categories.map((category) => (
                  <Button
                    key={category}
                    variant={selectedCategory === category ? 'default' : 'outline'}
                    onClick={() => setSelectedCategory(category)}
                    className="rounded-full"
                    data-testid={`filter-${category.toLowerCase()}`}
                  >
                    {getCategoryIcon(category)} {category}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Videos Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="videos-grid">
          {filteredVideos.map((video) => {
            const isCompleted = completedVideos.includes(video.id);
            return (
              <Card key={video.id} className="bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 overflow-hidden">
                <div className="relative">
                  <div className="bg-gray-900 aspect-video flex items-center justify-center">
                    <img 
                      src={`https://img.youtube.com/vi/${video.youtubeId}/maxresdefault.jpg`}
                      alt={video.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'https://via.placeholder.com/480x270/1f2937/ffffff?text=Video+Demo';
                      }}
                    />
                    <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                      {isCompleted ? (
                        <CheckCircle className="w-12 h-12 text-green-500" />
                      ) : (
                        <PlayCircle className="w-12 h-12 text-white" />
                      )}
                    </div>
                  </div>
                  
                  <div className="absolute top-3 left-3 flex gap-2">
                    <Badge className="bg-black/70 text-white border-0">
                      {video.duration} min
                    </Badge>
                    {!isCompleted && (
                      <Badge className="bg-yellow-500 text-white border-0">
                        +{video.points} pts
                      </Badge>
                    )}
                  </div>
                  
                  {isCompleted && (
                    <div className="absolute top-3 right-3">
                      <Badge className="bg-green-500 text-white border-0">
                        ✅ Completado
                      </Badge>
                    </div>
                  )}
                </div>
                
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start mb-2">
                    <Badge className={getDifficultyColor(video.difficulty)}>
                      {video.difficulty}
                    </Badge>
                    <span className="text-sm text-gray-500">{getCategoryIcon(video.category)} {video.category}</span>
                  </div>
                  <CardTitle className="text-lg leading-tight">{video.title}</CardTitle>
                  <CardDescription className="text-sm">
                    {video.description}
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="pt-0">
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 mb-4">
                    <div>
                      <span className="font-medium">Instructor:</span>
                      <div>{video.instructor}</div>
                    </div>
                    <div>
                      <span className="font-medium">Equipo:</span>
                      <div>{video.equipment}</div>
                    </div>
                  </div>
                </CardContent>
                
                <CardFooter className="pt-0">
                  {isCompleted ? (
                    <Button
                      className="w-full bg-green-600 hover:bg-green-700 text-white"
                      onClick={() => setSelectedVideo(video)}
                      data-testid={`rewatch-video-${video.id}`}
                    >
                      <PlayCircle className="w-4 h-4 mr-2" />
                      Ver de Nuevo
                    </Button>
                  ) : (
                    <Button
                      className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
                      onClick={() => setSelectedVideo(video)}
                      data-testid={`watch-video-${video.id}`}
                    >
                      <PlayCircle className="w-4 h-4 mr-2" />
                      Ver Video (+{video.points} pts)
                    </Button>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* No Results */}
        {filteredVideos.length === 0 && (
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-12 text-center">
              <Video className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No se encontraron videos</h3>
              <p className="text-gray-600">Intenta con otros filtros o términos de búsqueda</p>
            </CardContent>
          </Card>
        )}

        {/* Video Player Modal */}
        <Dialog open={!!selectedVideo} onOpenChange={() => setSelectedVideo(null)}>
          <DialogContent className="max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold">{selectedVideo?.title}</DialogTitle>
              <DialogDescription>
                {selectedVideo?.description}
              </DialogDescription>
            </DialogHeader>
            
            {selectedVideo && (
              <div className="space-y-4">
                {/* YouTube Embed */}
                <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden">
                  <iframe
                    width="100%"
                    height="100%"
                    src={`https://www.youtube.com/embed/${selectedVideo.youtubeId}?autoplay=1&rel=0`}
                    title={selectedVideo.title}
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className="w-full h-full"
                  ></iframe>
                </div>
                
                {/* Video Info */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold mb-2">Detalles del Video</h4>
                    <div className="space-y-1 text-sm">
                      <p><span className="font-medium">Duración:</span> {selectedVideo.duration} minutos</p>
                      <p><span className="font-medium">Instructor:</span> {selectedVideo.instructor}</p>
                      <p><span className="font-medium">Categoría:</span> {selectedVideo.category}</p>
                      <p><span className="font-medium">Dificultad:</span> {selectedVideo.difficulty}</p>
                      <p><span className="font-medium">Equipo:</span> {selectedVideo.equipment}</p>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Recompensas</h4>
                    <div className="space-y-2">
                      <Badge className="bg-yellow-100 text-yellow-800">
                        +{selectedVideo.points} puntos al completar
                      </Badge>
                      {completedVideos.length + 1 >= 5 && (
                        <Badge className="bg-purple-100 text-purple-800">
                          🎓 Badge "Aprendiz Visual" desbloqueado
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Complete Video Button */}
                {!completedVideos.includes(selectedVideo.id) && (
                  <Button
                    onClick={() => {
                      completeVideo(selectedVideo.id);
                      setSelectedVideo(null);
                    }}
                    className="w-full bg-green-600 hover:bg-green-700 text-white"
                    data-testid="complete-video-btn"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Marcar como Completado (+{selectedVideo.points} pts)
                  </Button>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default VideoGallery;