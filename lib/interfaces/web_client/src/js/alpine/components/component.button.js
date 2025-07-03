export default (btn_class = null) => ({
  button: {
    "class": `${btn_class} px-6 py-3 rounded-full text-sm font-medium text-white bg-pink-700 border border-pink-200 shadow-sm inline-flex items-center cursor-pointer`,
  },
});