import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const CurrencyContext = createContext();

export const CurrencyProvider = ({ children }) => {
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [rates, setRates] = useState({});
  const [isLoadingRates, setIsLoadingRates] = useState(false);

  useEffect(() => {
    const storedCurrency = localStorage.getItem('selectedCurrency');
    if (storedCurrency) {
      setSelectedCurrency(storedCurrency);
    }
    // No initial fetch, will be triggered by components
  }, []);

  const setCurrency = (currency) => {
    setSelectedCurrency(currency);
    localStorage.setItem('selectedCurrency', currency);
  };

  const ensureRates = useCallback(async (sourceCurrencies, targetCurrency) => {
    const uniqueSourceCurrencies = [...new Set(sourceCurrencies)].filter(Boolean);
    const requiredRates = uniqueSourceCurrencies
      .filter(source => source !== targetCurrency)
      .map(source => `${source}_${targetCurrency}`);

    const missingRates = requiredRates.filter(rateKey => !rates[rateKey]);

    if (missingRates.length === 0) {
      return;
    }

    setIsLoadingRates(true);
    try {
      const ratePromises = missingRates.map(rateKey => {
        const [from_currency, to_currency] = rateKey.split('_');
        return fetch(`http://127.0.0.1:8000/exchange_rate?from_currency=${from_currency}&to_currency=${to_currency}`)
          .then(res => res.json())
          .then(data => ({ key: rateKey, ...data }));
      });

      const newRatesResults = await Promise.allSettled(ratePromises);

      const newRates = newRatesResults.reduce((acc, result) => {
        if (result.status === 'fulfilled' && result.value.rate) {
          acc[result.value.key] = result.value.rate;
        } else if (result.status === 'rejected' || !result.value.rate) {
          console.error('Failed to fetch rate:', result.reason || result.value);
        }
        return acc;
      }, {});

      setRates(prevRates => ({ ...prevRates, ...newRates }));

    } catch (error) {
      console.error('Error fetching exchange rates:', error);
    } finally {
      setIsLoadingRates(false);
    }
  }, [rates, setRates]);


  return (
    <CurrencyContext.Provider value={{ selectedCurrency, setCurrency, rates, isLoadingRates, ensureRates }}>
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = () => {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
};
