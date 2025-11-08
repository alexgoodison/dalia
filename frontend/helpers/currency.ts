export const formatAmount = (amount?: number | null) => {
  if (amount === null || amount === undefined) {
    return "—";
  }

  return new Intl.NumberFormat(undefined, {
    style: "decimal",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};
