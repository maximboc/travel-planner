import React, { useState } from 'react';
import { Plane, ChevronDown, ChevronUp, Clock, ArrowRight, Calendar } from 'lucide-react';

export const FlightsBlock = ({ flightData, selectedIndex }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const flights = flightData || [];

  const formatPrice = (price, currency = 'USD') => {
    try {
      return new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: currency 
      }).format(parseFloat(price));
    } catch {
      return `${currency} ${price}`;
    }
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  const formatDuration = (duration) => {
    if (!duration) return 'N/A';
    const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
    if (match) {
      const hours = match[1] || '0';
      const minutes = match[2] || '0';
      return `${hours}h ${minutes}m`;
    }
    return duration;
  };

  const getStopsText = (stops) => {
    if (stops === 0) return 'Nonstop';
    if (stops === 1) return '1 stop';
    return `${stops} stops`;
  };

  return (
    <div className="bg-cyan-50 rounded-xl border border-cyan-100 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-cyan-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Plane className="w-5 h-5 text-cyan-600" />
          <span className="text-xs font-semibold text-cyan-900 uppercase">
            Flights Found ({flights.length})
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-cyan-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-cyan-600" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {flights.map((flight, i) => {
            const isSelected = selectedIndex === i;
            const outbound = flight.itineraries?.[0];
            const returnFlight = flight.itineraries?.[1];
            
            // Get first and last segments for minimal view
            const firstSegment = outbound?.segments?.[0];
            const lastSegment = outbound?.segments?.[outbound.segments.length - 1];

            return (
              <div
                key={i}
                className={`relative text-sm p-3 rounded-xl border transition-all duration-200 ${
                  isSelected
                    ? "bg-white border-cyan-500 shadow-md ring-1 ring-cyan-500"
                    : "bg-white/60 border-cyan-100 hover:border-cyan-300"
                }`}
              >
                {isSelected && (
                  <div className="absolute -top-2 -right-2 bg-cyan-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                    CHOSEN
                  </div>
                )}

                {/* Minimal Info (Always Shown) */}
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1">
                    {firstSegment && lastSegment && (
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-800">
                          {firstSegment.departure_airport}
                        </span>
                        <ArrowRight className="w-4 h-4 text-cyan-600" />
                        <span className="font-bold text-gray-800">
                          {lastSegment.arrival_airport}
                        </span>
                        {returnFlight && (
                          <>
                            <ArrowRight className="w-4 h-4 text-cyan-400" />
                            <span className="font-bold text-gray-800">
                              {firstSegment.departure_airport}
                            </span>
                          </>
                        )}
                      </div>
                    )}
                    {firstSegment && (
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDateTime(firstSegment.departure_time)}
                        {returnFlight && ' • Round trip'}
                        {!returnFlight && ' • One way'}
                      </p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-bold text-cyan-700">
                      {formatPrice(flight.price, flight.currency)}
                    </p>
                    <p className="text-[10px] text-gray-500">total</p>
                  </div>
                </div>

                {/* Detailed Info (Shown When Selected) */}
                {isSelected && (
                  <div className="mt-3 pt-3 border-t border-cyan-100 space-y-3">
                    {/* Outbound Itinerary */}
                    {outbound && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Plane className="w-4 h-4 text-cyan-600" />
                          <p className="text-xs font-semibold text-gray-700 uppercase">
                            Outbound
                          </p>
                        </div>
                        {outbound.segments?.map((segment, idx) => (
                          <div
                            key={idx}
                            className="bg-cyan-50 rounded-lg p-2.5 space-y-2"
                          >
                            {/* Route */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-bold text-gray-800">
                                  {segment.departure_airport}
                                </span>
                                <ArrowRight className="w-4 h-4 text-cyan-500" />
                                <span className="text-sm font-bold text-gray-800">
                                  {segment.arrival_airport}
                                </span>
                              </div>
                              {segment.airline && (
                                <span className="text-[10px] bg-cyan-200 text-cyan-700 px-2 py-0.5 rounded uppercase font-semibold">
                                  {segment.airline}
                                </span>
                              )}
                            </div>

                            {/* Times */}
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div>
                                <p className="text-gray-500">Departure</p>
                                <p className="font-medium text-gray-800">
                                  {formatDateTime(segment.departure_time)}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500">Arrival</p>
                                <p className="font-medium text-gray-800">
                                  {formatDateTime(segment.arrival_time)}
                                </p>
                              </div>
                            </div>

                            {/* Duration & Stops */}
                            <div className="flex items-center gap-3 text-xs pt-1 border-t border-cyan-100">
                              {segment.duration && (
                                <div className="flex items-center gap-1 text-gray-600">
                                  <Clock className="w-3 h-3" />
                                  <span>{formatDuration(segment.duration)}</span>
                                </div>
                              )}
                              {segment.stops !== undefined && (
                                <div className="flex items-center gap-1 text-gray-600">
                                  <span className={segment.stops === 0 ? 'text-green-600 font-medium' : ''}>
                                    {getStopsText(segment.stops)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Return Itinerary */}
                    {returnFlight && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Plane className="w-4 h-4 text-cyan-600 transform rotate-180" />
                          <p className="text-xs font-semibold text-gray-700 uppercase">
                            Return
                          </p>
                        </div>
                        {returnFlight.segments?.map((segment, idx) => (
                          <div
                            key={idx}
                            className="bg-cyan-50 rounded-lg p-2.5 space-y-2"
                          >
                            {/* Route */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-bold text-gray-800">
                                  {segment.departure_airport}
                                </span>
                                <ArrowRight className="w-4 h-4 text-cyan-500" />
                                <span className="text-sm font-bold text-gray-800">
                                  {segment.arrival_airport}
                                </span>
                              </div>
                              {segment.airline && (
                                <span className="text-[10px] bg-cyan-200 text-cyan-700 px-2 py-0.5 rounded uppercase font-semibold">
                                  {segment.airline}
                                </span>
                              )}
                            </div>

                            {/* Times */}
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div>
                                <p className="text-gray-500">Departure</p>
                                <p className="font-medium text-gray-800">
                                  {formatDateTime(segment.departure_time)}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500">Arrival</p>
                                <p className="font-medium text-gray-800">
                                  {formatDateTime(segment.arrival_time)}
                                </p>
                              </div>
                            </div>

                            {/* Duration & Stops */}
                            <div className="flex items-center gap-3 text-xs pt-1 border-t border-cyan-100">
                              {segment.duration && (
                                <div className="flex items-center gap-1 text-gray-600">
                                  <Clock className="w-3 h-3" />
                                  <span>{formatDuration(segment.duration)}</span>
                                </div>
                              )}
                              {segment.stops !== undefined && (
                                <div className="flex items-center gap-1 text-gray-600">
                                  <span className={segment.stops === 0 ? 'text-green-600 font-medium' : ''}>
                                    {getStopsText(segment.stops)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
