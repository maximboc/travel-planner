import { MapPin } from "lucide-react";

export const DestinationBlock = ({ plan, cityCode }) => (
  <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
    <div className="flex items-center gap-2 mb-2">
      <MapPin className="w-5 h-5 text-blue-600" />
      <span className="text-xs font-semibold text-blue-900 uppercase">
        Destination
      </span>
    </div>
    <p className="font-bold text-gray-800">{plan.destination || "---"}</p>
    {cityCode && (
      <p className="text-xs text-gray-600 mt-1">Code: {cityCode}</p>
    )}
  </div>
);
