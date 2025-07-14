import { parse } from "yaml";

export default () => ({

    init() {
        // Set initial value of generateNewGroupFile
        this.generateNewGroupFile = this.$store.data.dataGroupIsDirty;
        // Lock magic button if necessary
        this.$store.app.appMagicButtonIsLocked = this.$store.data.dataGroupIsDirty
            && !this.$store.data.dataGroupIsComplete;
        // Watch for changes in generateNewGroupFile
        this.$watch("generateNewGroupFile", (generateNewGroupFile) => {
            this.$store.app.appMagicButtonIsLocked = generateNewGroupFile
                && !this.$store.data.dataGroupIsComplete;
        });
        // Watch for changes in dataGroupIsComplete
        this.$watch("$store.data.dataGroupIsComplete", (isComplete) => {
            this.$store.app.appMagicButtonIsLocked = !isComplete
        });
    },

    destroy() {
        // On destroy, unlock magic button
        this.$nextTick(() =>  this.$store.app.appMagicButtonIsLocked = false);
    },

    generateNewGroupFile: false,

    generateStringInputFactory: (model) => ({

        ["x-model"]: model,
        
        [":class"]() {
            return this.generateNewGroupFile
                ? "disabled"
                : "opacity-25";
        },

        [":disable"]() {
            return this.generateNewGroupFile;
        },
    }),

    generateNumberInputFactory: (model) => ({

        ["x-model.number"]: model,
        
        [":class"]() {
            return this.generateNewGroupFile
                ? "disabled"
                : "opacity-25";
        },

        [":disable"]() {
            return this.generateNewGroupFile;
        },
    }),

    generateFieldLabel: {
        [":class"]() {
            return this.generateNewGroupFile
                ? ""
                : "opacity-25";
        }
    },

    magicButton: {

        label: "next",

        async ["action"]() {
            // If no generateNewGroupFile
            if (!this.generateNewGroupFile) {
                // Reset dataGroup
                this.$store.data.resetdataGroup();
                // Go to dropzone
                return this.navigationGoTo("dropzone");
            };
            // Make sure form data is complete
            if (!this.$store.data.dataGroupIsComplete)
                return;
            // Store api request 
            this.$store.api.apiRequest = {
                endpoint: "api/group",
                method: "POST",
                queryParams: {"language": "it"},
                bodyData: JSON.parse(JSON.stringify(this.$store.data.dataGroup))
            };
            // Call server
            this.$store.api.apiResponse = await this.apiHandleRequest(this.$store.api.apiRequest);
            // On api success
            if (this.$store.api.apiResponse.statusCode < 400) {
                // Notify
                this.toastShow(200, this.$t("toast.success"));
                // Save filename
                this.$store.data.dataFilename = 
                    this.$store.api.apiResponse.data.detail.metadata.filename;
                // Save yaml group data to store
                this.$store.data.dataYAML = 
                    this.$store.api.apiResponse.data.detail.rendered_group;
                // Save json group data to store
                this.$store.data.$dataJSON = parse(this.$store.data.dataYAML);
                // Go to dropzone
                this.navigationGoTo("dropzone");
            }
            // On api error
            if (this.$store.api.apiResponse.statusCode >= 400) {
                // Go to notify
                this.navigationGoTo("notify");
            }
        }
    }
});
