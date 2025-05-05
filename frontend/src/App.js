import React, { useState, useEffect } from 'react';
import { Loader, Camera, Upload, Play, Save, ChevronDown, Sparkles, Moon, Star, Sun } from 'lucide-react';
import './App.css';

// Backend API URL
const API_URL = "http://localhost:8000";

const AnimeOpeningGenerator = () => {
  const [images, setImages] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedVideo, setGeneratedVideo] = useState(null);
  const [videoTheme, setVideoTheme] = useState('action');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userName, setUserName] = useState('');
  const [generationProgress, setGenerationProgress] = useState(0);
  const [authToken, setAuthToken] = useState('');
  const [taskId, setTaskId] = useState(null);
  
  // Themes for anime openings
  const themes = [
    { 
      id: 'action', 
      name: 'Action/Adventure', 
      description: 'Epic battle scenes with powerful poses',
      icon: <Star className="w-8 h-8 text-yellow-400" />,
      bgClass: 'bg-red-500 bg-opacity-10'
    },
    { 
      id: 'romance', 
      name: 'Romance/Slice of Life', 
      description: 'Cherry blossoms and nostalgic moments',
      icon: <Moon className="w-8 h-8 text-pink-400" />,
      bgClass: 'bg-pink-500 bg-opacity-10'
    },
    { 
      id: 'fantasy', 
      name: 'Fantasy/Magic', 
      description: 'Mystical environments with magical effects',
      icon: <Sparkles className="w-8 h-8 text-purple-400" />,
      bgClass: 'bg-purple-500 bg-opacity-10'
    },
    { 
      id: 'scifi', 
      name: 'Sci-Fi/Cyberpunk', 
      description: 'Futuristic cityscapes with neon lights',
      icon: <Sun className="w-8 h-8 text-blue-400" />,
      bgClass: 'bg-blue-500 bg-opacity-10'
    },
    { 
      id: 'comedy', 
      name: 'Comedy/Parody', 
      description: 'Exaggerated expressions and funny moments',
      icon: <Sparkles className="w-8 h-8 text-green-400" />,
      bgClass: 'bg-green-500 bg-opacity-10'
    }
  ];

  // For hackathon demo - mock authentication
  const handleLogin = async () => {
    // In a real implementation, this would use Stytch's SDK
    // For hackathon, we'll use a mock token
    const mockToken = 'hackathon-demo-token-' + Math.random().toString(36).substring(2);
    setAuthToken(mockToken);
    setIsAuthenticated(true);
    setUserName("HackathonUser");
    
    // Store token in localStorage for persistence
    localStorage.setItem('auth_token', mockToken);
  };
  
  const handleLogout = () => {
    setAuthToken('');
    setIsAuthenticated(false);
    setUserName('');
    localStorage.removeItem('auth_token');
  };
  
  // Check for existing auth on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setAuthToken(storedToken);
      setIsAuthenticated(true);
      setUserName("HackathonUser");
    }
    
    // Add sparkle effects
    const addSparkles = () => {
      const container = document.querySelector('.container');
      if (!container) return;
      
      for (let i = 0; i < 5; i++) {
        const sparkle = document.createElement('div');
        sparkle.className = `sparkle sparkle-${i+1}`;
        container.appendChild(sparkle);
      }
    };
    
    addSparkles();
  }, []);

  // Handle file upload
  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    
    // Preview the images
    const imagePromises = files.map(file => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve({
          file,
          preview: e.target.result,
          name: file.name
        });
        reader.readAsDataURL(file);
      });
    });

    Promise.all(imagePromises).then(newImages => {
      setImages(prev => [...prev, ...newImages]);
    });
  };

  // Remove an image
  const removeImage = (index) => {
    setImages(images.filter((_, i) => i !== index));
  };

  // Check generation progress
  const checkGenerationProgress = async (taskId) => {
    try {
      const response = await fetch(`${API_URL}/api/generation-status/${taskId}`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Progress update:', data);
      
      setGenerationProgress(data.progress || 0);
      
      if (data.status === 'completed') {
        // Generation completed
        setIsGenerating(false);
        
        // Set the generated video URL
        if (data.result && data.result.video_url) {
          setGeneratedVideo(`${API_URL}${data.result.video_url}`);
        }
        return true;
      } else if (data.status === 'failed') {
        // Generation failed
        setIsGenerating(false);
        alert(`Generation failed: ${data.message}`);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error checking generation status:', error);
      return false;
    }
  };

  // Generate anime opening
  const generateOpening = async () => {
    if (images.length === 0) {
      alert("Please upload at least one image!");
      return;
    }
    
    setIsGenerating(true);
    setGenerationProgress(0);
    
    try {
      const formData = new FormData();
      images.forEach((image, i) => {
        formData.append('images', image.file);
      });
      formData.append('theme', videoTheme);
      
      // Include auth token in headers if available
      const headers = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }
      
      const response = await fetch(`${API_URL}/api/generate-opening`, {
        method: 'POST',
        body: formData,
        headers
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Generation started:', data);
      
      if (data.task_id) {
        // Store task ID for status checks
        setTaskId(data.task_id);
        
        // Poll for progress updates
        let completed = false;
        while (!completed && isGenerating) {
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
          completed = await checkGenerationProgress(data.task_id);
        }
      } else {
        // Fallback for demo purposes
        // Simulate progress
        for (let i = 0; i <= 100; i += 10) {
          setGenerationProgress(i);
          await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        setGeneratedVideo('/sample-anime-opening.mp4');
        setIsGenerating(false);
      }
    } catch (error) {
      console.error("Error generating anime opening:", error);
      setIsGenerating(false);
      alert("Failed to generate anime opening. Please try again.");
    }
  };

  // Save generated video
  const saveVideo = async () => {
    if (!isAuthenticated) {
      alert("Please log in to save your anime opening!");
      return;
    }
    
    try {
      // Include auth token in headers
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }
      
      const response = await fetch(`${API_URL}/api/save-opening`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          opening_id: taskId || 'latest',
          title: `My ${videoTheme.charAt(0).toUpperCase() + videoTheme.slice(1)} Anime Opening`
        })
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        alert("Your anime opening has been saved!");
      } else {
        alert("Failed to save your anime opening. Please try again.");
      }
    } catch (error) {
      console.error("Error saving anime opening:", error);
      alert("Failed to save your anime opening. Please try again.");
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="anime-title">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-pink-500 to-indigo-600 text-transparent bg-clip-text mb-2">
          アニメ Opening Generator
        </h1>
      </div>
      
      <p className="text-center text-lg mb-8">
        Transform you and your friends into epic anime characters!
      </p>

      {!isAuthenticated ? (
        <div className="flex justify-end mb-4">
          <button 
            onClick={handleLogin}
            className="btn"
          >
            Login with Stytch
          </button>
        </div>
      ) : (
        <div className="flex justify-end mb-4">
          <div className="card" style={{padding: '0.75rem', marginBottom: 0}}>
            <div className="flex items-center justify-between">
              <p className="text-gray-300">Welcome, {userName}! <span className="text-pink-400">★</span></p>
              <button 
                onClick={handleLogout}
                className="text-pink-400 hover:text-pink-300 text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      {isAuthenticated ? (
        <>
          <div className="card">
            <h2 className="text-2xl font-semibold mb-4">Step 1: Upload Photos</h2>
            
            <div className="mb-6">
              <div className="upload-area">
                <label className="flex flex-col items-center justify-center w-full h-64 cursor-pointer">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-12 h-12 mb-3 text-pink-400" />
                    <p className="mb-2 text-xl">
                      <span className="font-semibold text-pink-400">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-gray-400">PNG, JPG (MAX. 10MB each)</p>
                  </div>
                  <input 
                    type="file" 
                    className="hidden" 
                    multiple 
                    accept="image/*" 
                    onChange={handleImageUpload} 
                  />
                </label>
              </div>
            </div>

            {images.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4 fade-in">
                {images.map((image, index) => (
                  <div key={index} className="preview-thumbnail">
                    <img 
                      src={image.preview} 
                      alt={`Preview ${index}`} 
                      className="w-full h-32 object-cover rounded-lg"
                    />
                    <button
                      onClick={() => removeImage(index)}
                      className="remove-btn"
                    >
                      ×
                    </button>
                    <div className="mt-2 text-center text-sm text-gray-400">
                      Character {index + 1}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <h2 className="text-2xl font-semibold mb-4">Step 2: Choose Opening Theme</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {themes.map(theme => (
                <div 
                  key={theme.id}
                  onClick={() => setVideoTheme(theme.id)}
                  className={`theme-card ${videoTheme === theme.id ? 'selected' : ''} ${theme.bgClass}`}
                >
                  <div className="flex items-center mb-2">
                    {theme.icon}
                    <h3 className="font-medium text-lg ml-2">{theme.name}</h3>
                  </div>
                  <p className="text-gray-400 text-sm">{theme.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="text-center mt-8 mb-8">
            <button
              onClick={generateOpening}
              disabled={isGenerating || images.length === 0}
              className="btn pulse"
            >
              {isGenerating ? (
                <>
                  <Loader className="w-5 h-5 animate-spin mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Generate Anime Opening
                </>
              )}
            </button>
            
            {isGenerating && (
              <div className="mt-4 fade-in">
                <p className="text-gray-300 mb-2">Transforming your photos into anime...</p>
                <div className="progress-container">
                  <div className="progress-bar" style={{ width: `${generationProgress}%` }}></div>
                </div>
                <p className="text-sm text-gray-400">{generationProgress}% complete</p>
              </div>
            )}
          </div>

          {generatedVideo && (
            <div className="card fade-in">
              <h2 className="text-2xl font-semibold mb-4">Your Anime Opening</h2>
              
              <div className="video-container">
                <video
                  controls
                  className="video-player"
                  src={generatedVideo}
                />
                <div className="video-controls">
                  <button className="text-white"><Play /></button>
                  <div className="text-white">00:00 / 00:30</div>
                </div>
              </div>
              
              <div className="flex justify-center mt-4">
                <button
                  onClick={saveVideo}
                  className="btn"
                >
                  <Save className="w-5 h-5 mr-2" />
                  Save Opening
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="card text-center">
          <h2 className="text-2xl font-semibold mb-4">Welcome to Anime Opening Generator!</h2>
          <p className="text-gray-400 mb-6">
            Please log in to start creating your own anime openings.
          </p>
          <div className="flex justify-center">
            <Star className="w-8 h-8 text-pink-400 animate-pulse" />
          </div>
        </div>
      )}

      <footer className="footer">
        <p className="text-gray-400">Created for the Dumb Things Hackathon 2025</p>
        <p className="mt-1 text-xs text-gray-500">Powered by Replicate, OpenAI, Cloudflare, and Stytch</p>
        <div className="mt-4 flex justify-center gap-4">
          <Star className="w-4 h-4 text-pink-400" />
          <Moon className="w-4 h-4 text-indigo-400" />
          <Star className="w-4 h-4 text-yellow-400" />
        </div>
      </footer>
    </div>
  );
};

export default AnimeOpeningGenerator;