import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Plane,
  Calendar,
  DollarSign,
  MapPin,
  Hotel,
  Compass,
  Sun,
  Users,
  CheckCircle2,
  Loader2,
  PanelRight,
  PanelRightClose,
  AlertCircle,
  Trash2,
  Edit3,
  Plus,
  RotateCcw,
  Brain,
  Wrench,
  Sparkles,
} from "lucide-react";

export const TripDetailsSidebar = ({
  agentState,
  isEditing,
  editablePlan,
  setEditablePlan,
  onEdit,
  onUpdatePlan,
  onCancelEdit,
}) => {
  const plan = agentState.plan;
  const hasState = plan || agentState.adults || agentState.flight_data;

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6 sticky top-24 animate-in slide-in-from-right-10 duration-300">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-purple-600" />
          Trip Details
        </h2>
        {plan && !isEditing && (
          <button
            onClick={onEdit}
            className="text-purple-600 hover:text-purple-800"
          >
            <Edit3 className="w-4 h-4" />
          </button>
        )}
      </div>

      {!hasState ? (
        <p className="text-sm text-gray-500 italic">
          Details will appear as you chat...
        </p>
      ) : (
        <div className="space-y-4">
          {isEditing ? (
            <div className="space-y-4">
              {/* ... (Editing inputs remain unchanged) ... */}
              <div>
                <label className="text-xs font-semibold text-gray-600">
                  Destination
                </label>
                <input
                  type="text"
                  value={editablePlan.destination || ""}
                  onChange={(e) =>
                    setEditablePlan({
                      ...editablePlan,
                      destination: e.target.value,
                    })
                  }
                  className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600">
                  Departure Date
                </label>
                <input
                  type="text"
                  value={editablePlan.departure_date || ""}
                  onChange={(e) =>
                    setEditablePlan({
                      ...editablePlan,
                      departure_date: e.target.value,
                    })
                  }
                  className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600">
                  Arrival Date
                </label>
                <input
                  type="text"
                  value={editablePlan.arrival_date || ""}
                  onChange={(e) =>
                    setEditablePlan({
                      ...editablePlan,
                      arrival_date: e.target.value,
                    })
                  }
                  className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600">
                  Budget
                </label>
                <input
                  type="number"
                  value={editablePlan.budget || ""}
                  onChange={(e) =>
                    setEditablePlan({
                      ...editablePlan,
                      budget: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={onUpdatePlan}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg"
                >
                  Save
                </button>
                <button
                  onClick={onCancelEdit}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* ... (Destination, Dates, Budget, Passengers blocks remain unchanged) ... */}
              {plan && (
                <>
                  <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="w-5 h-5 text-blue-600" />
                      <span className="text-xs font-semibold text-blue-900 uppercase">
                        Destination
                      </span>
                    </div>
                    <p className="font-bold text-gray-800">
                      {plan.destination || "---"}
                    </p>
                    {agentState.city_code && (
                      <p className="text-xs text-gray-600 mt-1">
                        Code: {agentState.city_code}
                      </p>
                    )}
                  </div>

                  <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="w-5 h-5 text-purple-600" />
                      <span className="text-xs font-semibold text-purple-900 uppercase">
                        Dates
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-800">
                      {plan.departure_date ? `${plan.departure_date}` : "---"}
                    </p>
                    {plan.arrival_date && (
                      <p className="text-sm font-medium text-gray-800 mt-1">
                        to {plan.arrival_date}
                      </p>
                    )}
                  </div>

                  <div className="bg-pink-50 p-4 rounded-xl border border-pink-100">
                    <div className="flex items-center gap-2 mb-2">
                      <DollarSign className="w-5 h-5 text-pink-600" />
                      <span className="text-xs font-semibold text-pink-900 uppercase">
                        Budget
                      </span>
                    </div>
                    <p className="font-bold text-gray-800">
                      ${plan.budget || 0}
                    </p>
                  </div>
                </>
              )}

              {(agentState.adults > 0 ||
                agentState.children > 0 ||
                agentState.infants > 0) && (
                <div className="bg-orange-50 p-4 rounded-xl border border-orange-100">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-5 h-5 text-orange-600" />
                    <span className="text-xs font-semibold text-orange-900 uppercase">
                      Passengers
                    </span>
                  </div>
                  <div className="space-y-1 text-sm text-gray-700">
                    {agentState.adults > 0 && (
                      <p>Adults: {agentState.adults}</p>
                    )}
                    {agentState.children > 0 && (
                      <p>Children: {agentState.children}</p>
                    )}
                    {agentState.infants > 0 && (
                      <p>Infants: {agentState.infants}</p>
                    )}
                    {agentState.travel_class && (
                      <p className="text-xs text-gray-600 mt-2">
                        Class: {agentState.travel_class}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* FLIGHTS BLOCK */}
              {agentState.flight_data && agentState.flight_data.length > 0 && (
                <div className="bg-cyan-50 p-4 rounded-xl border border-cyan-100">
                  <div className="flex items-center gap-2 mb-2">
                    <Plane className="w-5 h-5 text-cyan-600" />
                    <span className="text-xs font-semibold text-cyan-900 uppercase">
                      Flights Found
                    </span>
                  </div>
                  <div className="space-y-2">
                    {agentState.flight_data.map((f, i) => (
                      <div
                        key={i}
                        className={`text-sm p-2 rounded-lg ${
                          agentState.selected_flight_index === i
                            ? "bg-cyan-200/50 border border-cyan-300"
                            : "bg-white/50"
                        }`}
                      >
                        <p className="font-bold">
                          {f.price} {f.currency}
                        </p>
                        <p className="text-xs">
                          Depart: {new Date(f.departure_time).toLocaleString()}
                        </p>
                        <p className="text-xs">
                          Arrive: {new Date(f.arrival_time).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* HOTELS BLOCK*/}
              {agentState.hotel_data &&
                agentState.hotel_data.hotels &&
                agentState.hotel_data.hotels.length > 0 && (
                  <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Hotel className="w-5 h-5 text-emerald-600" />
                      <span className="text-xs font-semibold text-emerald-900 uppercase">
                        Hotels Found
                      </span>
                    </div>
                    <div className="space-y-3">
                      {agentState.hotel_data.hotels.map((h, i) => {
                        const isSelected = agentState.selected_hotel_index === i;
                        return (
                          <div
                            key={i}
                            className={`relative text-sm p-3 rounded-xl border transition-all duration-200 ${
                              isSelected
                                ? "bg-white border-emerald-500 shadow-md ring-1 ring-emerald-500"
                                : "bg-white/60 border-emerald-100 hover:border-emerald-300"
                            }`}
                          >
                            {/* Selected Badge */}
                            {isSelected && (
                              <div className="absolute -top-2 -right-2 bg-emerald-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                                CHOSEN
                              </div>
                            )}

                            <div className="flex justify-between items-start gap-2">
                              <div>
                                <p className="font-bold text-gray-800 leading-tight">
                                  {h.name}
                                </p>
                                {h.rating && (
                                  <div className="flex items-center mt-1">
                                    <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded">
                                      ★ {h.rating}
                                    </span>
                                  </div>
                                )}
                              </div>
                              
                              {/* Price Display */}
                              {h.price && (
                                <div className="text-right shrink-0">
                                  <p className="font-bold text-emerald-700">
                                    {new Intl.NumberFormat('en-US', { style: 'currency', currency: h.currency || 'USD' }).format(h.price)}
                                  </p>
                                  <p className="text-[10px] text-gray-500">total</p>
                                </div>
                              )}
                            </div>

                            {/* Room Description */}
                            {h.description && (
                              <p className="text-xs text-gray-500 mt-2 line-clamp-2 leading-relaxed">
                                {h.description}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

              {/* ACTIVITIES BLOCK*/}
              {agentState.activity_data &&
                agentState.activity_data.length > 0 && (
                  <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Compass className="w-5 h-5 text-yellow-600" />
                      <span className="text-xs font-semibold text-yellow-900 uppercase">
                        Activities Found
                      </span>
                    </div>
                    <div className="space-y-3">
                      {agentState.activity_data.map((a, i) => (
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
                      ))}
                    </div>
                  </div>
                )}
            </>
          )}
        </div>
      )}
    </div>
  );
};
