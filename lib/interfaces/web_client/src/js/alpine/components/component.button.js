export default (btn_class) => ({
  cButton: {
    ["class"]: 
      `rounded-md ${btn_class} px-3.5 py-2.5 text-sm font-semibold text-white shadow-xs focus-visible:outline-2 focus-visible:outline-offset-2`,
  },
});