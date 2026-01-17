"use client";

import MapComponent from "@/components/Map";
import { useState, useEffect } from "react";
import { useLocation } from "@/hooks/use-location";
import { MapPin, PenTool, Type, Loader2 } from "lucide-react";
import clsx from "clsx";

type InputMode = 'draw' | 'type';

export default function Home() {
  const [mode, setMode] = useState<InputMode>('type');
  const [prompt, setPrompt] = useState("");
  const { latitude, longitude, error, loading: locationLoading, getCurrentLocation } = useLocation();

  // Auto-locate on mount (optional, maybe better on button click?)
  // Let's do it on button click to be polite.

  return (
    <main className="relative w-full h-full min-h-screen">
      <MapComponent />
      
      {/* Overlay UI Container */}
      <div className="absolute top-4 left-4 right-4 z-10 flex flex-col gap-4 max-w-md mx-auto sm:mx-0 sm:left-4 sm:right-auto pointer-events-none">
         <div className="bg-white/95 backdrop-blur-md p-5 rounded-2xl shadow-xl border border-zinc-200 pointer-events-auto transition-all duration-300 ease-in-out">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-1">
              PathArt
            </h1>
            <p className="text-xs text-zinc-500 mb-4 font-medium uppercase tracking-wider">
              AI-Powered Route Designer
            </p>
            
            {/* Mode Toggles */}
            <div className="flex bg-zinc-100 p-1 rounded-lg mb-4">
               <button 
                  onClick={() => setMode('type')}
                  className={clsx(
                    "flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-all duration-200",
                    mode === 'type' ? "bg-white text-black shadow-sm" : "text-zinc-500 hover:text-zinc-700"
                  )}
               >
                 <Type size={16} />
                 Type Prompt
               </button>
               <button 
                  onClick={() => setMode('draw')}
                  className={clsx(
                    "flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-all duration-200",
                    mode === 'draw' ? "bg-white text-black shadow-sm" : "text-zinc-500 hover:text-zinc-700"
                  )}
               >
                 <PenTool size={16} />
                 Draw Shape
               </button>
            </div>

            {/* Input Area */}
            <div className="flex flex-col gap-3">
              {mode === 'type' ? (
                <div className="relative">
                  <textarea 
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g., A running route shaped like a dinosaur..."
                    className="w-full h-24 p-3 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none bg-zinc-50 focus:bg-white"
                  />
                  <div className="absolute bottom-2 right-2 text-xs text-zinc-400">
                    {prompt.length}/200
                  </div>
                </div>
              ) : (
                <div className="h-24 flex items-center justify-center bg-zinc-50 border border-dashed border-zinc-300 rounded-lg text-sm text-zinc-500">
                  <p>Draw mode coming soon!</p>
                </div>
              )}

              {/* Location Picker */}
              <div className="flex items-center gap-2">
                 <button 
                   onClick={getCurrentLocation}
                   disabled={locationLoading}
                   className={clsx(
                     "flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-colors w-full",
                     latitude ? "bg-green-50 text-green-700 border-green-200" : "bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50"
                   )}
                 >
                   {locationLoading ? <Loader2 size={14} className="animate-spin" /> : <MapPin size={14} />}
                   {latitude ? "Location Acquired" : "Use Current Location"}
                 </button>
              </div>
              
              {error && <p className="text-xs text-red-500 px-1">{error}</p>}

              {/* Generate Button */}
              <button className="w-full bg-black text-white py-2.5 rounded-lg text-sm font-medium hover:bg-zinc-800 active:scale-[0.98] transition-all flex items-center justify-center gap-2">
                Generate Route
              </button>
            </div>
         </div>
      </div>
    </main>
  );
}
