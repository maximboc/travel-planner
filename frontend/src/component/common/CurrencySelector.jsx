import React from 'react';
import { useCurrency } from '../../context/CurrencyContext';
import { DollarSign } from 'lucide-react';

export const CurrencySelector = () => {
  const { selectedCurrency, setCurrency } = useCurrency();

  const handleCurrencyChange = (event) => {
    setCurrency(event.target.value);
  };

  return (
    <div className="relative inline-flex items-center group">
      <select
        value={selectedCurrency}
        onChange={handleCurrencyChange}
        className="appearance-none bg-gray-100 border border-gray-200 text-gray-700 py-1.5 pl-8 pr-3 rounded-md leading-tight focus:outline-none focus:bg-white focus:border-purple-300 text-sm font-medium transition-colors cursor-pointer"
      >
        <option value="USD">USD</option>
        <option value="EUR">EUR</option>
      </select>
      <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-2 text-gray-500 group-hover:text-purple-600 transition-colors">
        <DollarSign className="w-4 h-4" />
      </div>
    </div>
  );
};
