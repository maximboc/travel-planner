import { Users } from "lucide-react";

export const PassengersBlock = ({ agentState }) => (
  <div className="bg-orange-50 p-4 rounded-xl border border-orange-100">
    <div className="flex items-center gap-2 mb-2">
      <Users className="w-5 h-5 text-orange-600" />
      <span className="text-xs font-semibold text-orange-900 uppercase">
        Passengers
      </span>
    </div>
    <div className="space-y-1 text-sm text-gray-700">
      {agentState.adults > 0 && <p>Adults: {agentState.adults}</p>}
      {agentState.children > 0 && <p>Children: {agentState.children}</p>}
      {agentState.infants > 0 && <p>Infants: {agentState.infants}</p>}
      {agentState.travel_class && (
        <p className="text-xs text-gray-600 mt-2">
          Class: {agentState.travel_class}
        </p>
      )}
    </div>
  </div>
);
