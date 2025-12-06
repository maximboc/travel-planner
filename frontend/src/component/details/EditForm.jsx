
export const EditForm = ({ editablePlan, setEditablePlan, onSave, onCancel }) => (
  <div className="space-y-4">
    <div>
      <label className="text-xs font-semibold text-gray-600">Destination</label>
      <input
        type="text"
        value={editablePlan.destination || ""}
        onChange={(e) =>
          setEditablePlan({ ...editablePlan, destination: e.target.value })
        }
        className="w-full mt-1 p-2 border border-gray-300 rounded-lg text-sm"
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
          setEditablePlan({ ...editablePlan, departure_date: e.target.value })
        }
        className="w-full mt-1 p-2 border border-gray-300 rounded-lg text-sm"
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
          setEditablePlan({ ...editablePlan, arrival_date: e.target.value })
        }
        className="w-full mt-1 p-2 border border-gray-300 rounded-lg text-sm"
      />
    </div>
    <div>
      <label className="text-xs font-semibold text-gray-600">Budget</label>
      <input
        type="number"
        value={editablePlan.budget || ""}
        onChange={(e) =>
          setEditablePlan({
            ...editablePlan,
            budget: parseFloat(e.target.value) || 0,
          })
        }
        className="w-full mt-1 p-2 border border-gray-300 rounded-lg text-sm"
      />
    </div>
    <div className="flex gap-2 pt-2">
      <button
        onClick={onSave}
        className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
      >
        Save
      </button>
      <button
        onClick={onCancel}
        className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg text-sm font-medium transition-colors"
      >
        Cancel
      </button>
    </div>
  </div>
);
