import React, { useState, useEffect } from 'react';
import { Loader, Camera, Upload, Play, Save, ChevronDown, Sparkles } from 'lucide-react';
import './App.css';

const AnimeOpeningGenerator = () => {
  const [images, setImages] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedVideo, setGeneratedVideo] = useState(null);
  const [videoTheme, setVideoTheme] = useState('action');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userName, setUserName] = useState('');
  
  // Themes for anime openings
  const themes = [
    { id: 'action', name: 'Action/Adventure', description: 'Epic battle scenes with powerful poses' },
    { id: 'romance', name: 'Romance/Slice of Life', description: 'Cherry blossoms and nostalgic moments' },
    { id: 'fantasy', name: 'Fantasy/Magic', description: 'Mystical environments with magical effects' },
    { id: 'scifi', name: 'Sci-Fi/Cyberpunk', description: 'Futuristic cityscapes with neon lights' },
    { id: 'comedy', name: 'Comedy/Parody', description: 'Exaggerated expressions and funny moments' }
  ];

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

  // Generate anime opening
  const generateOpening = async () => {
    if (images.length === 0) {
      alert("Please upload at least one image!");
      return;
    }
    
    setIsGenerating(true);
    
    try {
      // Mock API call for hackathon demo
      // In real implementation, this would call our backend API
      setTimeout(() => {
        setGeneratedVideo('/sample-anime-opening.mp4');
        setIsGenerating(false);
      }, 5000);
      
      // Actual API call would look like:
      /*
      const formData = new FormData();
      images.forEach((image, i) => {
        formData.append('images', image.file);
      });
      formData.append('theme', videoTheme);
      
      const response = await fetch('/api/generate-opening', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      setGeneratedVideo(data.videoUrl);
      setIsGenerating(false);
      */
    } catch (error) {
      console.error("Error generating anime opening:", error);
      setIsGenerating(false);
      alert("Failed to generate anime opening. Please try again.");
    }
  };

  // Login with Stytch
  const handleLogin = async () => {
    // In a real implementation, this would use Stytch's SDK
    setIsAuthenticated(true);
    setUserName("HackathonUser");
  };

  // Save generated video
  const saveVideo = async () => {
    if (!isAuthenticated) {
      alert("Please log in to save your anime opening!");
      return;
    }
    
    // In a real implementation, this would save to the user's account
    alert("Your anime opening has been saved!");
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <header className="text-center mb-12">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-pink-500 to-indigo-600 text-transparent bg-clip-text mb-2">
          Anime Opening Generator
        </h1>
        <p className="text-gray-600 text-xl">
          Transform you and your friends into epic anime characters!
        </p>
      </header>

      {!isAuthenticated ? (
        <div className="flex justify-end mb-4">
          <button 
            onClick={handleLogin}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition-colors"
          >
            Login with Stytch
          </button>
        </div>
      ) : (
        <div className="flex justify-end mb-4">
          <p className="text-gray-600">Welcome, {userName}!</p>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold mb-4">1. Upload Photos</h2>
        
        <div className="mb-6">
          <div className="flex items-center justify-center w-full">
            <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 border-gray-300 hover:bg-gray-100">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className="w-10 h-10 mb-3 text-gray-400" />
                <p className="mb-2 text-sm text-gray-500">
                  <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-gray-500">PNG, JPG (MAX. 10MB each)</p>
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
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4">
            {images.map((image, index) => (
              <div key={index} className="relative">
                <img 
                  src={image.preview} 
                  alt={`Preview ${index}`} 
                  className="w-full h-32 object-cover rounded-lg"
                />
                <button
                  onClick={() => removeImage(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold mb-4">2. Choose Opening Theme</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {themes.map(theme => (
            <div 
              key={theme.id}
              onClick={() => setVideoTheme(theme.id)}
              className={`border-2 rounded-lg p-4 cursor-pointer transition-colors ${
                videoTheme === theme.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <h3 className="font-medium text-lg">{theme.name}</h3>
              <p className="text-gray-500 text-sm">{theme.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="text-center mb-8">
        <button
          onClick={generateOpening}
          disabled={isGenerating}
          className="bg-gradient-to-r from-pink-500 to-indigo-600 text-white px-8 py-3 rounded-lg font-medium text-lg flex items-center gap-2 mx-auto hover:opacity-90 transition-opacity disabled:opacity-70"
        >
          {isGenerating ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Generate Anime Opening
            </>
          )}
        </button>
      </div>

      {generatedVideo && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Your Anime Opening</h2>
          
          <div className="aspect-video bg-black rounded-lg overflow-hidden mb-4">
            <video
              controls
              className="w-full h-full"
              src={generatedVideo}
            />
          </div>
          
          <div className="flex justify-center">
            <button
              onClick={saveVideo}
              className="bg-green-600 text-white px-6 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700 transition-colors"
            >
              <Save className="w-5 h-5" />
              Save Opening
            </button>
          </div>
        </div>
      )}

      <footer className="text-center text-gray-500 text-sm mt-12">
        <p>Created for the Dumb Things Hackathon 2025</p>
        <p className="mt-1">Powered by Replicate, OpenAI, Cloudflare, and Stytch</p>
      </footer>
    </div>
  );
};

export default AnimeOpeningGenerator;