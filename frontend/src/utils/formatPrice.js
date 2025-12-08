
/**
 * Formats a price into a currency string, optionally converting it to a target currency.
 * @param {number} price The numerical price.
 * @param {string} targetCurrency The currency to convert to and format in (e.g., 'USD', 'EUR').
 * @param {string} [originalCurrency='USD'] The original currency of the price.
 * @param {number} [usdToEurRate=1] The exchange rate from USD to EUR.
 * @param {number} [eurToUsdRate=1] The exchange rate from EUR to USD.
 * @returns {string} The formatted currency string.
 */
export const formatPrice = (price, targetCurrency, originalCurrency = 'USD', usdToEurRate = 1, eurToUsdRate = 1) => {
  if (typeof price !== 'number' && typeof price !== 'string') {
    return 'N/A';
  }

  const numericPrice = parseFloat(price);
  if (isNaN(numericPrice)) {
    return 'N/A';
  }

  let priceToFormat = numericPrice;

  // Only perform conversion if original and target currencies are different
  if (originalCurrency !== targetCurrency) {
    if (originalCurrency === 'USD' && targetCurrency === 'EUR') {
      priceToFormat = numericPrice * usdToEurRate;
    } else if (originalCurrency === 'EUR' && targetCurrency === 'USD') {
      priceToFormat = numericPrice * eurToUsdRate;
    }
    // For other currency combinations (e.g., JPY to EUR, USD to JPY),
    // we currently don't have the rates in context.
    // So, for now, we will simply format the original price in the target currency
    // without actual numerical conversion if it's not USD <-> EUR.
    // In a more robust system, we would fetch or have all cross-rates.
  }

  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: targetCurrency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(priceToFormat);
  } catch (error) {
    console.error("Error formatting price:", error);
    return `${targetCurrency} ${priceToFormat.toFixed(2)}`;
  }
};

