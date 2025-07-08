export default () => ({

    editRowId: null,

    reportProjectFieldFactory: (key) => ({
        ["@mouseenter"]() {
            this.editRowId = key;
        }
    }),

    reportProjectFieldIdFactory: (key) =>
    ({
        ["x-text"]() {
            return this.$t(`groupData.${key}`);
        }
    }),

    reportProjectFieldSpanFactory: (key, value) =>
    ({
        ["x-show"]() {
            return this.editRowId != key;
        },

        ["x-text"]() {
            return value;
        },

        ["@choicechange.window"]($event) {
            if (key != this.editRowId) return;
            this.$el.innerText = $event.detail;
        },
    }),

    reportProjectFieldInputFactory: (key, value) =>
    ({
        ["x-show"]() {
            return this.editRowId == key;
        },

        [":value"]() {
            return value;
        },

        ["@keyup.enter.window"]() {
            if (key != this.editRowId) return;
            this.$el.blur();
        },

        ["@mouseleave"]($event) {
            if (key != this.editRowId) return;
            this.$dispatch("choicechange", $event.target.value);
            this.$store.abgrid.reportDataJSON[key] = $event.target.value;
        },

        ["@blur"]($event) {
            if (key != this.editRowId) return;
            this.$dispatch("choicechange", $event.target.value);
            this.$store.abgrid.reportDataJSON[key] = $event.target.value;
        },
    }),

    reportChoiceFactory: (choice) =>
    ({
        ["@mouseenter"]() {
            const [key] = Object.keys(choice);
            this.editRowId = key;
        }
    }),

    reportChoiceIdFactory: (choice) =>
    ({
        ["x-text"]() {
            const [key] = Object.keys(choice);
            return key;
        }
    }),

    reportChoiceSpanFactory: (choice) =>
    ({
        ["x-text"]() {
            const [value] = Object.values(choice);
            return value;
        },

        ["x-show"]() {
            const [key] = Object.keys(choice);
            return this.editRowId != key;
        },


        ["@choicechange.window"]($event) {
            const [key] = Object.keys(choice);
            if (key != this.editRowId) return;
            this.$el.innerText = $event.detail;
        },
    }),

    reportChoiceInputFactory: (choice, rootKey, index) =>
    ({
        ["x-show"]() {
            const [key] = Object.keys(choice);
            return this.editRowId == key;
        },

        [":value"]() {
            const [value] = Object.values(choice);
            return value;
        },

        ["@keyup.enter.window"]() {
            const [key] = Object.keys(choice);
            if (key != this.editRowId) return;
            this.$el.blur();
        },

        ["@mouseleave"]($event) {
            const [key] = Object.keys(choice);
            if (key != this.editRowId) return;
            this.$dispatch("choicechange", $event.target.value);
            this.$store.abgrid.reportDataJSON[rootKey][index] = { [key]: $event.target.value };
        },

        ["@blur"]($event) {
            const [key] = Object.keys(choice);
            if (key != this.editRowId) return;
            this.$dispatch("choicechange", $event.target.value);
            this.$store.abgrid.reportDataJSON[rootKey][index] = { [key]: $event.target.value };
        },
    }),

    magicButton: {

        label: "next",

        ["action"]() {
            this.navigationGoTo("notify");
        }
    }
});
