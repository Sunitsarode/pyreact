
export const getCurrencySymbol = (symbol) => {
  if (symbol.endsWith('.NS')) {
    return '₹';
  }
  // Default to USD for others, can be expanded
  return '$';
};

export const formatPrice = (price, symbol) => {
  if (price === null || price === undefined || price === 0) {
    return 'N/A';
  }
  
  const currencySymbol = getCurrencySymbol(symbol);
  return `${currencySymbol}${price.toFixed(2)}`;
};
