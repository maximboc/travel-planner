import { useEffect, useMemo } from 'react';
import { DollarSign, TrendingDown, TrendingUp, Loader } from "lucide-react";
import { useCurrency } from "../../context/CurrencyContext";
import { formatPrice } from "../../utils/formatPrice";

// A simple utility to get a value from another currency into the target currency
const convertToCurrency = (amount, fromCurrency, toCurrency, rates) => {
  const numericAmount = parseFloat(amount);
  if (isNaN(numericAmount) || !fromCurrency || !toCurrency || !rates) return 0;
  if (fromCurrency === toCurrency) return numericAmount;

  const rateKey = `${fromCurrency}_${toCurrency}`;
  const rate = rates[rateKey];

  if (rate === undefined) {
    console.warn(`Exchange rate not found for ${rateKey}`);
    return 0; // Or handle as an error
  }
  
  return numericAmount * rate;
};


export const BudgetBlock = ({
  budget,
  budgetCurrency,
  flights,
  selectedFlightIndex,
  hotels,
  selectedHotelIndex,
  activities,
}) => {
  const { selectedCurrency, rates, ensureRates, isLoadingRates } = useCurrency();

  // 1. Collect all source currencies from props
  useEffect(() => {
    const currencies = new Set([budgetCurrency]);
    if (flights) flights.forEach(f => currencies.add(f.currency));
    if (hotels) hotels.forEach(h => h.offers?.forEach(o => currencies.add(o.price.currency)));
    if (activities) activities.forEach(a => currencies.add(a.currency));
    
    ensureRates(Array.from(currencies), selectedCurrency);
  }, [budgetCurrency, flights, hotels, activities, selectedCurrency, ensureRates]);

  // 2. Calculate total spent in the *selected* currency
  const totalSpent = useMemo(() => {
    let spent = 0;

    // Flight cost
    const flight = flights?.[selectedFlightIndex];
    if (flight) {
      spent += convertToCurrency(flight.price, flight.currency, selectedCurrency, rates);
    }

    // Hotel cost
    const hotel = hotels?.[selectedHotelIndex];
    if (hotel) {
      const offer = hotel.offers?.[0];
      if (offer?.price?.total) {
        spent += convertToCurrency(offer.price.total, offer.price.currency, selectedCurrency, rates);
      }
    }

    // Activities cost
    if (activities) {
      activities.forEach(activity => {
        if (activity.amount) {
          spent += convertToCurrency(activity.amount, activity.currency, selectedCurrency, rates);
        }
      });
    }

    return spent;
  }, [flights, selectedFlightIndex, hotels, selectedHotelIndex, activities, selectedCurrency, rates]);

  // 3. Convert total budget to the selected currency for comparison
  const totalBudgetInSelectedCurrency = useMemo(() => {
    return convertToCurrency(budget, budgetCurrency, selectedCurrency, rates);
  }, [budget, budgetCurrency, selectedCurrency, rates]);

  const remaining = totalBudgetInSelectedCurrency - totalSpent;
  const spentPercentage = totalBudgetInSelectedCurrency > 0 ? (totalSpent / totalBudgetInSelectedCurrency) * 100 : 0;

  const getProgressBarColor = () => {
    if (spentPercentage > 100) return "bg-red-500";
    if (spentPercentage > 80) return "bg-yellow-500";
    return "bg-green-500";
  };
  
  return (
    <div className="bg-gray-50 p-4 rounded-xl border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <DollarSign className="w-5 h-5 text-gray-600" />
        <span className="text-xs font-semibold text-gray-800 uppercase">
          Budget Overview
        </span>
      </div>
      
      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-3">
        <div
          className={`h-2.5 rounded-full ${getProgressBarColor()}`}
          style={{ width: `${Math.min(spentPercentage, 100)}%` }}
        ></div>
      </div>
      
      {/* Financial Breakdown */}
      <div className="grid grid-cols-3 divide-x divide-gray-200">
        <div className="px-2 text-center">
          <p className="text-xs text-gray-500">Total</p>
          <p className="font-bold text-gray-800 text-sm">
            {formatPrice(totalBudgetInSelectedCurrency, selectedCurrency, selectedCurrency, rates)}
          </p>
        </div>
        {isLoadingRates ? (
          <>
            <div className="px-2 text-center">
              <p className="text-xs text-gray-500">Spent</p>
              <p className="font-bold text-red-600 text-sm flex items-center justify-center">
                <Loader className="w-4 h-4 animate-spin" />
              </p>
            </div>
            <div className="px-2 text-center">
              <p className="text-xs text-gray-500">Remaining</p>
              <p className="font-bold text-green-600 text-sm flex items-center justify-center">
                <Loader className="w-4 h-4 animate-spin" />
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="px-2 text-center">
              <p className="text-xs text-gray-500">Spent</p>
              <p className="font-bold text-red-600 text-sm">
                {formatPrice(totalSpent, selectedCurrency, selectedCurrency, rates)}
              </p>
            </div>
            <div className="px-2 text-center">
              <p className="text-xs text-gray-500">Remaining</p>
              <p className={`font-bold text-sm ${remaining < 0 ? 'text-red-600' : 'text-green-600'}`}>
                {formatPrice(remaining, selectedCurrency, selectedCurrency, rates)}
              </p>
            </div>
          </>
        )}
      </div>

      {!isLoadingRates && spentPercentage > 100 && (
         <div className="mt-3 text-xs text-red-600 bg-red-50 p-2 rounded-lg flex items-center gap-2">
            <TrendingDown className="w-4 h-4" />
            <span>You are <span className='font-bold'>{formatPrice(Math.abs(remaining), selectedCurrency, selectedCurrency, rates)}</span> over budget.</span>
         </div>
      )}
       {!isLoadingRates && spentPercentage <= 100 && spentPercentage > 0 && (
         <div className="mt-3 text-xs text-green-700 bg-green-50 p-2 rounded-lg flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            <span>You have <span className='font-bold'>{formatPrice(remaining, selectedCurrency, selectedCurrency, rates)}</span> left to spend.</span>
         </div>
      )}
    </div>
  );
};
