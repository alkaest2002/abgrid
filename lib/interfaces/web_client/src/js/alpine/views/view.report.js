export default () => ({

    editRowId: null,

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
        [":value"]() {
            const [value] = Object.values(choice);
            return value;
        },

        ["@keyup.enter.window"]() {
            const [key] = Object.keys(choice);
            if (key != this.editRowId) return;
            this.$el.blur();
        },
        
        ["@change"]($event) {
            const [key] = Object.keys(choice);
            if (key != this.editRowId) return;
            this.$dispatch("choicechange", $event.target.value);
            window.Alpine.store("abgrid").reportData[rootKey][index] = { [key]: $event.target.value };
        },

        ["x-show"]() {
            const [key] = Object.keys(choice);
            return this.editRowId == key;
        }
    }),

    magicButton: {

        label: "next",

        ["action"]() {
            this.navigationGoTo("notify");
        }
    }
});
