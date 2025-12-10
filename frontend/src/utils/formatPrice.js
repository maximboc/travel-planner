/**
 * Formats a price into a currency string, optionally converting it to a target currency.
 * @param {number} price The numerical price.
 * @param {string} targetCurrency The currency to convert to and format in (e.g., 'USD', 'EUR').
 * @param {string} originalCurrency The original currency of the price.
 * @param {object} rates A dictionary of exchange rates (e.g., { 'USD_EUR': 0.92 }).
 * @returns {string} The formatted currency string.
 */
export const formatPrice = (price, targetCurrency, originalCurrency, rates) => {
  if (typeof price !== 'number' && typeof price !== 'string') {
    return 'N/A';
  }

  const numericPrice = parseFloat(price);
  if (isNaN(numericPrice)) {
    return 'N/A';
  }

  let priceToFormat = numericPrice;
  let currencyToDisplay = targetCurrency;
  let displayOriginalAsSuffix = '';

  if (originalCurrency && originalCurrency !== targetCurrency) {
    const rateKey = `${originalCurrency}_${targetCurrency}`;
    const rate = rates[rateKey];

    if (rate) {
      priceToFormat = numericPrice * rate;
    } else {
      // Rate not found, format in original currency and indicate it's not converted
      currencyToDisplay = originalCurrency;
      displayOriginalAsSuffix = ` (${originalCurrency}*)`;
    }
  }

  try {
    // Determine locale based on currency for accurate formatting
    let locale;
    switch (currencyToDisplay) {
      case 'EUR':
        locale = 'de-DE'; // Use German locale for Euro formatting (€1.234,56)
        break;
      case 'GBP':
        locale = 'en-GB'; // Use British locale for Pound formatting (£1,234.56)
        break;
      default:
        locale = 'en-US'; // Default to US locale
    }

    const formattedPrice = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currencyToDisplay,
      minimumFractionDigits: 2, // Always show 2 decimal places for consistency
      maximumFractionDigits: 2,
    }).format(priceToFormat);
    
    return formattedPrice + (displayOriginalAsSuffix || '');
  } catch (error) {
    // Fallback for invalid currency codes
    if (error instanceof RangeError) {
      return `${originalCurrency} ${numericPrice.toFixed(2)}*`;
    }
    console.error("Error formatting price:", error);
    return `${targetCurrency} ${priceToFormat.toFixed(2)}`;
  }
};
