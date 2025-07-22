import { parse } from "yaml";

export default () => ({

    init() {

        // Perform some checks
        this.$nextTick(() => {
            
            // Set initial value of generateNewGroupFile
            this.generateNewGroupFile = this.$store.data.dataGroupIsDirty;
            
            // Lock magic button if necessary
            this.$store.app.appMagicButtonIsLocked = this.$store.data.dataGroupIsDirty
                && !this.$store.data.dataGroupIsComplete;
        });

        // Watch for changes in generateNewGroupFile
        this.$watch("generateNewGroupFile", (generateNewGroupFile) => {
            this.$store.app.appMagicButtonIsLocked = generateNewGroupFile
                && !this.$store.data.dataGroupIsComplete;
            if (!generateNewGroupFile)
                this.$store.data.resetdDataGroup();
        });
        
        // Watch for changes in dataGroupIsComplete
        this.$watch("$store.data.dataGroupIsComplete", (isComplete) => {
            this.$store.app.appMagicButtonIsLocked = 
                this.$store.data.dataGroupIsDirty && !isComplete;
        });
    },

    generateNewGroupFile: false,

    generateStringInputFactory: (model) => ({

        ["x-model"]: model,

        ["@click"]($event) {
           $event.target.classList.remove("bg-red-100");
           $event.target.classList.add("bg-white");
        },
        
        [":disabled"]() {
            return !this.generateNewGroupFile;
        },
    }),

    generateNumberInputFactory: (model) => ({

        ["x-model.number"]: model,

        ["@click"]($event) {
           $event.target.classList.remove("bg-red-100");
           $event.target.classList.add("bg-white");
        },
        
        [":disabled"]() {
            return !this.generateNewGroupFile;
        },
    }),

    generateFieldLabel: {
        [":class"]() {
            return this.generateNewGroupFile
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

            // If no generateNewGroupFile
            if (!this.generateNewGroupFile) {
                // Reset dataGroup
                this.$store.data.resetdDataGroup();
                // Go to dropzone (either data or empty)
                return this.$store.data.dataYAML 
                    ? this.navigationGoTo("dropzone.data")
                    : this.navigationGoTo("dropzone.empty");
            };
            
            // Create api request 
            const apiRequest = {
                endpoint: "api/group",
                method: "POST",
                queryParams: {"language": "it"},
                // Ensure POJO
                bodyData: JSON.parse(JSON.stringify(this.$store.data.dataGroup))
            };
            
            // Make api request to server
            const { statusCode, data } =  await this.apiHandleRequest(apiRequest);
            
            // On api request success
            if (statusCode == 200) {
                // Extract detail from data
                const { detail } = data;
                // Save filename to store
                this.$store.data.dataFilename = detail.metadata.filename;
                // Save YAML data to store
                this.$store.data.dataYAML = detail.rendered_group;
                // Save JSON data to store
                this.$store.data.dataJSON = parse(this.$store.data.dataYAML);
                // Go to data dropzone
                this.navigationGoTo("dropzone.data");
            // On api request error
            } else {
                // Extract data
                const { detail } = this.$store.api.apiResponse.data;
                // Go to api error notify if detail is not an array
                !Array.isArray(detail) && this.navigationGoTo("notify.error.api");
                // Add visual cue to fields with errors
                detail.forEach(({ location }) => {
                    this.$refs[location].classList.remove("bg-white");
                    this.$refs[location].classList.add("bg-red-100");
                })
            }
        }
    }
});
