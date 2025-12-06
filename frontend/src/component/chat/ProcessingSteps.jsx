import { CheckCircle2, Loader2 } from 'lucide-react'

const nodeDisplayNames = {
  planner_agent: "Planning Trip",
  city_resolver: "Resolving Cities",
  passenger_agent: "Processing Passengers",
  flight_agent: "Searching Flights",
  hotel_agent: "Finding Hotels",
  activity_agent: "Discovering Activities",
  compiler: "Compiling Itinerary",
  reviewer: "Reviewing Plan",
};

export const ProcessingSteps = ({ steps }) => (
  <div className="flex justify-start">
    <div className="bg-blue-50 border border-blue-200 rounded-2xl px-6 py-4 max-w-[85%]">
      <div className="flex items-center gap-2 mb-3">
        <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
        <span className="text-sm font-semibold text-blue-900">
          Processing...
        </span>
      </div>
      <div className="space-y-2">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center gap-2 text-sm">
            {step.status === "completed" ? (
              <CheckCircle2 className="w-4 h-4 text-green-500" />
            ) : (
              <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
            )}
            <span
              className={
                step.status === "completed"
                  ? "text-gray-600"
                  : "text-blue-900 font-medium"
              }
            >
              {nodeDisplayNames[step.node] || step.node}
            </span>
          </div>
        ))}
      </div>
    </div>
  </div>
);
