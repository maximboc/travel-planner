import { Calendar } from "lucide-react";

export const DatesBlock = ({ plan }) => (
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
);
