import { useEffect } from 'react';
import { DollarSign } from "lucide-react";
import { useCurrency } from "../../context/CurrencyContext";
import { formatPrice } from "../../utils/formatPrice";

export const BudgetBlock = ({ plan }) => {
  const { selectedCurrency, rates, ensureRates } = useCurrency();

  useEffect(() => {
    if (plan?.budget_currency) {
      ensureRates([plan.budget_currency], selectedCurrency);
    }
  }, [plan?.budget_currency, selectedCurrency, ensureRates]);

  return (
    <div className="bg-pink-50 p-4 rounded-xl border border-pink-100">
      <div className="flex items-center gap-2 mb-2">
        <DollarSign className="w-5 h-5 text-pink-600" />
        <span className="text-xs font-semibold text-pink-900 uppercase">
          Budget
        </span>
      </div>
      <p className="font-bold text-gray-800">{formatPrice(plan.budget || 0, selectedCurrency, plan.budget_currency || 'USD', rates)}</p>
    </div>
  );
};
