export default () => ({

    resetButton: {

        [":class"]() { 
            return !this.$store.abgrid.groupDataIsComplete
                ? "opacity-50 cursor-not-allowed"
                : ""
        },

        ["@click"]() {
            this.$store.abgrid.resetGroupData();
        }
    },

    generateGroupButton: {

        [":class"]() { 
            return !this.$store.abgrid.groupDataIsComplete
                ? "opacity-50 cursor-not-allowed"
                : ""
        },
        
        ["@click"]() {
            this.$store.abgrid.resetGroupData();
        }
    },

    magicButton: {

        label: "next",

        ["action"]() {
            this.navigationGoTo("dropzone");
        }
    }
});
