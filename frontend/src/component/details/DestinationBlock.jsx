import React from 'react';
import { MapPin } from 'lucide-react';

export const DestinationBlock = ({ plan, cityCode, destinationName }) => {
  const getGoogleMapsLink = (destination) => {
    if (!destination) return null;
    return `http://maps.google.com/?q=${encodeURIComponent(destination)}`;
  };
  
  const mapsLink = getGoogleMapsLink(destinationName || plan.destination);

  return (
    <div className="bg-purple-50 rounded-xl border border-purple-100 p-4">
      <h3 className="text-xs font-semibold text-purple-900 uppercase mb-3">
        Destination
      </h3>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-bold text-lg text-gray-800">
            {destinationName || plan.destination}
          </p>
          {cityCode && (
            <p className="text-sm text-gray-500">
              {plan.destination}
            </p>
          )}
        </div>
        {mapsLink && (
          <a
            href={mapsLink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm text-purple-600 hover:text-purple-700 hover:underline shrink-0"
          >
            <MapPin className="w-4 h-4" />
            View on Map
          </a>
        )}
      </div>
      {plan.reason && (
        <p className="text-xs text-gray-600 mt-2 pt-2 border-t border-purple-100">
          <strong>Reason for visit:</strong> {plan.reason}
        </p>
      )}
    </div>
  );
};
