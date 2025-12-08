import React, { createContext, useContext, useState, useEffect } from 'react';

const CurrencyContext = createContext();

export const CurrencyProvider = ({ children }) => {
  const [selectedCurrency, setSelectedCurrency] = useState('USD'); // Default currency
  const [usdToEurRate, setUsdToEurRate] = useState(1);
  const [eurToUsdRate, setEurToUsdRate] = useState(1);
  const [isLoadingExchangeRate, setIsLoadingExchangeRate] = useState(false);

  const fetchRates = async () => {
    setIsLoadingExchangeRate(true);
    try {
      const [usdToEurResponse, eurToUsdResponse] = await Promise.all([
        fetch('http://127.0.0.1:8000/exchange_rate?from_currency=USD&to_currency=EUR'),
        fetch('http://127.0.0.1:8000/exchange_rate?from_currency=EUR&to_currency=USD')
      ]);

      const usdToEurData = await usdToEurResponse.json();
      const eurToUsdData = await eurToUsdResponse.json();

      if (usdToEurResponse.ok) setUsdToEurRate(usdToEurData.rate);
      else console.error('Failed to fetch USD to EUR rate:', usdToEurData.detail || usdToEurData);

      if (eurToUsdResponse.ok) setEurToUsdRate(eurToUsdData.rate);
      else console.error('Failed to fetch EUR to USD rate:', eurToUsdData.detail || eurToUsdData);

    } catch (error) {
      console.error('Error fetching exchange rates:', error);
      setUsdToEurRate(1);
      setEurToUsdRate(1);
    } finally {
      setIsLoadingExchangeRate(false);
    }
  };

  useEffect(() => {
    const storedCurrency = localStorage.getItem('selectedCurrency');
    if (storedCurrency) {
      setSelectedCurrency(storedCurrency);
    }
    fetchRates(); // Fetch rates on initial load
  }, []); // Empty dependency array means this runs once on mount

  const setCurrency = (currency) => {
    setSelectedCurrency(currency);
    localStorage.setItem('selectedCurrency', currency);
    // Rates are already fetched, no need to re-fetch on simple selection change
  };

  return (
    <CurrencyContext.Provider value={{ selectedCurrency, setCurrency, usdToEurRate, eurToUsdRate, isLoadingExchangeRate }}>
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
