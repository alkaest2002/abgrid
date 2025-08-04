/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export default () => ({

    init() {

        // Perform initial checks
        this.$nextTick(() => {

            // Set initial value of groupNewFile
            this.groupNewFile = this.$store.data.dataGroupIsDirty;

            // Lock magic button if necessary
            this.$store.app.appMagicButtonIsLocked = this.$store.data.dataGroupIsDirty
                && !this.$store.data.dataGroupIsComplete;
        });

        // Watch for changes in groupNewFile
        this.$watch("groupNewFile", (groupNewFile) => {
            this.$store.app.appMagicButtonIsLocked = groupNewFile
                && !this.$store.data.dataGroupIsComplete;
            if (!groupNewFile) {
                // Reset data group
                this.$store.data.resetdDataGroup();
                // Get all input elements
                const inputFields = document.getElementsByTagName("input");
                // Remove error classes
                Array.prototype.slice.call(inputFields).forEach($el => {
                    $el.type != "checkbox" && $el.classList.remove("bg-red-100");
                    $el.type != "checkbox" && $el.classList.add("bg-white");
                });
            }
        });

        // Watch for changes in dataGroupIsComplete
        this.$watch("$store.data.dataGroupIsComplete", (isComplete) => {
            this.$store.app.appMagicButtonIsLocked =
                this.$store.data.dataGroupIsDirty && !isComplete;
        });
    },

    groupNewFile: false,

    groupStringInputFactory: (model) => ({

        ["x-model"]: model,

        ["@click"]($event) {
            $event.target.classList.remove("bg-red-100");
            $event.target.classList.add("bg-white");
        },

        [":disabled"]() {
            return !this.groupNewFile;
        },
    }),

    groupNumberInputFactory: (model) => ({

        ["x-model.number"]: model,

        ["@click"]($event) {
            $event.target.classList.remove("bg-red-100");
            $event.target.classList.add("bg-white");
        },

        [":disabled"]() {
            return !this.groupNewFile;
        },
    }),

    groupFieldLabel: {
        [":class"]() {
            return this.groupNewFile
                ? "opacity-100"
                : "opacity-25";
        }
    },

    magicButton: {

        label: "next",

        async ["action"]() {
            // Do nothing if group data is incomplete
            if (this.$store.data.dataGroupIsDirty && !this.$store.data.dataGroupIsComplete)
                return;

            // If no groupNewFile
            if (!this.groupNewFile) {
                // Go to dropzone (either data or empty)
                return this.$store.data.dataYAML
                    ? this.navigationGoTo("dropzone.data")
                    : this.navigationGoTo("dropzone.empty");
            };

            // Create api request 
            const apiRequest = {
                endpoint: "api/group",
                method: "POST",
                queryParams: { "language": "it" },
                // Ensure POJO
                bodyData: JSON.parse(JSON.stringify(this.$store.data.dataGroup))
            };

            // Make api request to server
            const { statusCode, data: { detail } } = await this.apiProcessRequest(apiRequest);

            // On api success
            if (statusCode == 200) {
                // Go to data dropzone page
                this.navigationGoTo("dropzone.data");
            // On api queue error
            } else if (statusCode == 429) {
                // Navigate to queue notification page
                this.navigationGoTo("notify.queue");
            // On any other apierror
            } else {
                // If detail is not an array
                if (!Array.isArray(detail)) {
                    // Go to api error notification page
                    return this.navigationGoTo("notify.error.api")
                };
                // Add visual cue to fields with errors
                detail.forEach(({ location }) => {
                    this.$refs[location].classList.remove("bg-white");
                    this.$refs[location].classList.add("bg-red-100");
                })
            }
        }
    }
});
