import { useState } from 'react'
import {
  Compass,
  ChevronDown,
  ChevronUp,
  MapPin,
} from "lucide-react";

export const ActivitiesBlock = ({ activityData, defaultOpen = false }) => {
  const [isExpanded, setIsExpanded] = useState(defaultOpen);
  
  // Determine visibility
  const shouldShow = isExpanded || defaultOpen;

  const getGoogleMapsLink = (activity) => {
    if (!activity) return null;
    const query = encodeURIComponent(`${activity.name}, ${activity.location?.city_code}`);
    return `http://maps.google.com/?q=${query}`;
  };

  return (
    <div className="bg-yellow-50 rounded-xl border border-yellow-100 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-yellow-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Compass className="w-5 h-5 text-yellow-600" />
          <span className="text-xs font-semibold text-yellow-900 uppercase">
            Activities Found ({activityData.length})
          </span>
        </div>
        {shouldShow ? (
          <ChevronUp className="w-4 h-4 text-yellow-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-yellow-600" />
        )}
      </button>
      
      {shouldShow && (
        <div className="px-4 pb-4 space-y-3">
          {activityData.map((a, i) => {
            const mapsLink = getGoogleMapsLink(a);
            return (
            <div
              key={i}
              className="group relative bg-white/60 hover:bg-white border border-yellow-100 hover:border-yellow-300 p-3 rounded-xl transition-all duration-200"
            >
              <div className="flex justify-between items-start gap-2">
                <h4 className="font-bold text-gray-800 text-sm leading-tight">
                  {a.name}
                </h4>
                {a.price && (
                  <span className="shrink-0 text-xs font-bold text-yellow-700 bg-yellow-100 px-2 py-1 rounded-md">
                    {a.price}
                  </span>
                )}
              </div>

              {mapsLink && (
                <a
                  href={mapsLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-yellow-600 hover:text-yellow-700 hover:underline mt-2"
                >
                  <MapPin className="w-3.5 h-3.5" />
                  View on Google Maps
                </a>
              )}

              {a.description && (
                <p className="text-xs text-gray-500 mt-2 line-clamp-2 leading-relaxed">
                  {a.description}
                </p>
              )}

              {a.booking_link && (
                <a
                  href={a.booking_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 flex items-center justify-center w-full py-1.5 text-xs font-medium text-yellow-700 bg-yellow-50 hover:bg-yellow-100 rounded-lg transition-colors border border-yellow-200 hover:border-yellow-300"
                >
                  Book Activity
                </a>
              )}
            </div>
          )})}
        </div>
      )}
    </div>
  );
};