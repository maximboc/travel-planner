import React, { useState } from 'react';
import { Hotel, ChevronDown, ChevronUp, Phone, Calendar, Users, Bed } from 'lucide-react';

export const HotelsBlock = ({ hotelData, selectedIndex, defaultOpen = false }) => {
  const [isExpanded, setIsExpanded] = useState(defaultOpen);
  const hotels = hotelData?.hotels || [];

  // Determine visibility
  const shouldShow = isExpanded || defaultOpen;

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

  const getBookingComLink = (hotel) => {
    if (!hotel) return null;
    const query = encodeURIComponent(`${hotel.name} ${hotel.location?.city_code}`);
    return `https://www.booking.com/searchresults.html?ss=${query}`;
  };

  return (
    <div className="bg-emerald-50 rounded-xl border border-emerald-100 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-emerald-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Hotel className="w-5 h-5 text-emerald-600" />
          <span className="text-xs font-semibold text-emerald-900 uppercase">
            Hotels Found ({hotels.length})
          </span>
        </div>
        {shouldShow ? (
          <ChevronUp className="w-4 h-4 text-emerald-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-emerald-600" />
        )}
      </button>

      {shouldShow && (
        <div className="px-4 pb-4 space-y-3">
          {hotels.map((hotel, i) => {
            const isSelected = selectedIndex === i;
            const firstOffer = hotel.offers?.[0];
            const bookingLink = getBookingComLink(hotel);

            return (
              <div
                key={hotel.hotel_id || i}
                className={`relative text-sm p-3 rounded-xl border transition-all duration-200 ${
                  isSelected
                    ? "bg-white border-emerald-500 shadow-md ring-1 ring-emerald-500"
                    : "bg-white/60 border-emerald-100 hover:border-emerald-300"
                }`}
              >
                {isSelected && (
                  <div className="absolute -top-2 -right-2 bg-emerald-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                    CHOSEN
                  </div>
                )}

                {/* Header Info */}
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1">
                    <p className="font-bold text-gray-800 leading-tight">
                      {hotel.name}
                    </p>
                    {hotel.location?.city_code && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {hotel.location.city_code}
                      </p>
                    )}
                  </div>
                  {firstOffer?.price && (
                    <div className="text-right shrink-0">
                      <p className="font-bold text-emerald-700">
                        {formatPrice(firstOffer.price.total, firstOffer.price.currency)}
                      </p>
                      <p className="text-[10px] text-gray-500">total</p>
                    </div>
                  )}
                </div>

                {/* Detailed Info */}
                <div className="mt-3 pt-3 border-t border-emerald-100 space-y-3">
                  {/* Location & Contact */}
                  <div className="space-y-2">
                    {hotel.contact?.phone && (
                      <div className="flex items-center gap-1.5 text-xs text-gray-600">
                        <Phone className="w-3.5 h-3.5" />
                        <span>{hotel.contact.phone}</span>
                      </div>
                    )}
                    {hotel.contact?.fax && (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500">
                        <Phone className="w-3.5 h-3.5" />
                        <span>Fax: {hotel.contact.fax}</span>
                      </div>
                    )}
                  </div>

                  {/* Offers */}
                  {hotel.offers && hotel.offers.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-gray-700 uppercase">
                        Available Offers ({hotel.offers.length})
                      </p>
                      {hotel.offers.map((offer, idx) => (
                        <div
                          key={offer.offer_id || idx}
                          className="bg-emerald-50 rounded-lg p-2.5 space-y-2"
                        >
                          <div className="flex items-center gap-3 text-xs">
                            <div className="flex items-center gap-1 text-gray-600">
                              <Calendar className="w-3 h-3" />
                              <span>{offer.check_in} → {offer.check_out}</span>
                            </div>
                            <div className="flex items-center gap-1 text-gray-600">
                              <Users className="w-3 h-3" />
                              <span>{offer.guests} guest{offer.guests !== 1 ? 's' : ''}</span>
                            </div>
                          </div>

                          {offer.room && (
                            <div className="space-y-1">
                              <div className="flex items-center gap-1.5">
                                <Bed className="w-3 h-3 text-gray-500" />
                                <span className="text-xs font-medium text-gray-700">
                                  {offer.room.room_type}
                                </span>
                              </div>
                              {(offer.room.beds || offer.room.bed_type) && (
                                <p className="text-xs text-gray-500 ml-4.5">
                                  {offer.room.beds && `${offer.room.beds} bed${offer.room.beds !== 1 ? 's' : ''}`}
                                  {offer.room.beds && offer.room.bed_type && ' • '}
                                  {offer.room.bed_type}
                                </p>
                              )}
                              {offer.room.description && (
                                <p className="text-xs text-gray-600 ml-4.5 line-clamp-2">
                                  {offer.room.description}
                                </p>
                              )}
                            </div>
                          )}

                          <div className="flex justify-between items-end pt-1.5 border-t border-emerald-100">
                            <div className="space-y-0.5">
                              {offer.board_type && (
                                <p className="text-[10px] text-gray-500 uppercase">
                                  {offer.board_type}
                                </p>
                              )}
                              {offer.price.avg_nightly && (
                                <p className="text-xs text-gray-600">
                                  {formatPrice(offer.price.avg_nightly, offer.price.currency)}/night
                                </p>
                              )}
                              {offer.price.taxes && (
                                <p className="text-[10px] text-gray-500">
                                  + {formatPrice(offer.price.taxes, offer.price.currency)} taxes
                                </p>
                              )}
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-bold text-emerald-700">
                                {formatPrice(offer.price.total, offer.price.currency)}
                              </p>
                            </div>
                          </div>

                          {(offer.cancellation_policy || bookingLink) && (
                            <div className="space-y-1.5 pt-1.5 border-t border-emerald-100">
                              {offer.cancellation_policy && (
                                <p className="text-[10px] text-gray-500">
                                  {offer.cancellation_policy}
                                </p>
                              )}
                              {bookingLink && (
                                <a
                                  href={bookingLink}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-block text-xs text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 rounded-lg transition-colors"
                                >
                                  Book Now
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};