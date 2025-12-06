import { MapPin, Edit3, Download } from "lucide-react";
import { ActivitiesBlock } from './ActivitiesBlock'
import { BudgetBlock } from './BudgetBlock'
import { DatesBlock } from "./DatesBlock";
import { HotelsBlock } from './HotelsBlock'
import { EditForm } from './EditForm'
import { PassengersBlock } from './PassengerBlock'
import { FlightsBlock } from './FlightsBlock'
import { DestinationBlock } from './DestinationBlock'

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

  const handleDownload = () => {
    if (!plan) return;

    const { city_code, flight_data, selected_flight_index, hotel_data, selected_hotel_index } = agentState;

    // Helper to format currency
    const fmt = (val) => val ? `$${val}` : 'N/A';

    // Construct the text content
    let content = `✈️ TRIP ITINERARY: ${plan.destination || city_code}\n`;
    content += `==========================================\n\n`;
    
    content += `📅 DATES\n`;
    content += `From: ${plan.departure_date}\nTo:   ${plan.arrival_date}\n\n`;
    
    content += `💰 BUDGET & INTERESTS\n`;
    content += `Budget: ${fmt(plan.budget)}\nInterests: ${plan.interests}\n\n`;
    
    content += `👥 TRAVELERS\n`;
    content += `Adults: ${agentState.adults || 1}, Children: ${agentState.children || 0}\n\n`;

    // Flight Details
    if (flight_data && selected_flight_index !== null && flight_data[selected_flight_index]) {
      const flight = flight_data[selected_flight_index];
      content += `🛫 FLIGHT DETAILS\n`;
      content += `Airline: ${flight.airline}\n`;
      content += `Price: ${fmt(flight.price)}\n`;
      content += `Flight Number: ${flight.flight_number}\n`;
      content += `Duration: ${flight.duration}\n\n`;
    }

    // Hotel Details
    if (hotel_data && hotel_data.hotels && selected_hotel_index !== null) {
      const hotel = hotel_data.hotels[selected_hotel_index];
      content += `🏨 HOTEL DETAILS\n`;
      content += `Name: ${hotel.name}\n`;
      if(hotel.offers?.[0]?.price?.total) {
         content += `Total Cost: ${hotel.offers[0].price.total} ${hotel.offers[0].price.currency}\n`;
      }
      content += `Address: ${hotel.location?.city_code || 'N/A'}\n`;
    }

    // Create the blob and trigger download
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Trip_to_${plan.destination || 'itinerary'}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6 sticky top-24 animate-in slide-in-from-right-10 duration-300">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-purple-600" />
          Trip Details
        </h2>
        
        <div className="flex gap-2">
          {plan && !isEditing && (
            <button
              onClick={handleDownload}
              className="text-gray-400 hover:text-purple-600 transition-colors p-1"
              title="Download Itinerary"
            >
              <Download className="w-4 h-4" />
            </button>
          )}

          {plan && !isEditing && (
            <button
              onClick={onEdit}
              className="text-gray-400 hover:text-purple-600 transition-colors p-1"
              title="Edit trip details"
            >
              <Edit3 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {!hasState ? (
        <p className="text-sm text-gray-500 italic">
          Details will appear as you chat...
        </p>
      ) : (
        <div className="space-y-4">
          {isEditing ? (
            <EditForm
              editablePlan={editablePlan}
              setEditablePlan={setEditablePlan}
              onSave={onUpdatePlan}
              onCancel={onCancelEdit}
            />
          ) : (
            <>
              {plan && (
                <>
                  <DestinationBlock plan={plan} cityCode={agentState.city_code} />
                  <DatesBlock plan={plan} />
                  <BudgetBlock plan={plan} />
                </>
              )}

              {(agentState.adults > 0 ||
                agentState.children > 0 ||
                agentState.infants > 0) && (
                <PassengersBlock agentState={agentState} />
              )}

              {agentState.flight_data && agentState.flight_data.length > 0 && (
                <FlightsBlock
                  flightData={agentState.flight_data}
                  selectedIndex={agentState.selected_flight_index}
                />
              )}

              {agentState.hotel_data &&
                agentState.hotel_data.hotels &&
                agentState.hotel_data.hotels.length > 0 && (
                  <HotelsBlock
                    hotelData={agentState.hotel_data}
                    selectedIndex={agentState.selected_hotel_index}
                  />
                )}

              {agentState.activity_data &&
                agentState.activity_data.length > 0 && (
                  <ActivitiesBlock activityData={agentState.activity_data} />
                )}
            </>
          )}
        </div>
      )}
    </div>
  );
};
