<script>
    import Select from "svelte-select";
    import { Jumper } from "svelte-loading-spinners";

    let genImgUrl = "";
    let genVideoUrl = "";

    let generatingImage = false;

    let modelArray = [
        {
            value: "dalle",
            label: "🌐 General",
            possibilities: "faces",
        },
        {
            value: "aphantasia",
            label: "✨ Dreamy",
            possibilities: "anything you want",
        },
        {
            value: "stylegan",
            label: "😗 Faces",
            possibilities: "faces",
        },
    ];

    let selectedModel = modelArray[0];

    let singleCreationActive = false;
    let collaborationActive = false;

    let generationConfig = {
        imageGeneration: false,
        videoGeneration: false,
    };

    let generationReady = false;

    let promptPlaceholderArray = [
        "The moustache of Salvador Dali",
        "CHANEL alien collection",
        "Birds wearing CHANEL",
        "Roses made of CHANEL",
        "CHANEL exotic jewelry collection",
        "Flowers made of diamonds",
    ];
    let prompt = "";

    function handleSelect(event) {
        selectedModel = event.detail;
    }

    function activateSingleCreation() {
        singleCreationActive = !singleCreationActive;
        collaborationActive = false;
    }

    function activateCollaboration() {
        collaborationActive = !collaborationActive;
        singleCreationActive = false;
    }

    function updateGenerationState() {
        for (var key in generationConfig) {
            if (generationConfig[key]) {
                generationReady = true;
                return;
            }
        }

        generationReady = false;
    }

    async function generate() {
        generatingImage = true;

        const serverURL = "http://localhost:8000";

        let params = {
            prompt: prompt,
            model: selectedModel.value,
        };

        params = Object.assign({}, params, generationConfig);

        let fetchURL = new URL(`${serverURL}/generate`);
        fetchURL.search = new URLSearchParams(params).toString();

        console.log("FETCHING DATA");
        const res = await fetch(fetchURL.toString(), {
            method: "GET",
        });

        const resultDict = await res.json();
        console.log("RESULTS", resultDict);

        genImgUrl = resultDict["imgUrl"];
        genVideoUrl = resultDict["videoUrl"];

        generatingImage = false;
    }
</script>

<h1>🥸 Bigotis Editor</h1>
<h3>Select a style</h3>
<Select
    items={modelArray}
    selectedValue={selectedModel}
    on:select={handleSelect}
/>

<h3>Select a mode</h3>
<div class="btn-container">
    <button on:click={activateSingleCreation}>Single Creation</button>
    <button on:click={activateCollaboration}>Colaboration</button>
</div>

{#if singleCreationActive}
    <h3>What do you want to generate?</h3>
    <div class="input-container">
        <input
            bind:value={prompt}
            placeholder={promptPlaceholderArray[
                Math.floor(Math.random() * promptPlaceholderArray.length)
            ]}
        />
    </div>

    {#if prompt != ""}
        <div class="label-container">
            <label>
                <input
                    type="checkbox"
                    bind:checked={generationConfig["imageGeneration"]}
                    on:click={() => window.setTimeout(updateGenerationState, 0)}
                />
                Image Generation
            </label>
            <label>
                <input
                    type="checkbox"
                    bind:checked={generationConfig["videoGeneration"]}
                    on:click={() => window.setTimeout(updateGenerationState, 0)}
                />
                Video Generation
            </label>

            {#if generationReady}
                {#if !generatingImage}
                    <div class="btn-container" style="margin-top: 20px">
                        <button on:click={generate}>Generate</button>
                    </div>
                {:else}
                    <div style="margin-top: 10px">
                        <Jumper
                            size="60"
                            color="#BE3CC6"
                            unit="px"
                            duration="1.3s"
                        />
                    </div>
                {/if}
            {/if}
        </div>

        {#if genImgUrl != ""}
            <h2>Generated Image</h2>
            <img
                style="margin-top: 20px"
                src={genImgUrl}
                alt="Generated Image"
            />
        {/if}

        {#if genVideoUrl != ""}
            <h2>Generated Video</h2>
            <video controls>
                <source src={genVideoUrl} type="video/mp4" />
                Your browser does not support mp4...
            </video>
        {/if}
    {/if}
{:else if collaborationActive}
    Collaboration
{/if}

<style>
    .input-container input {
        width: 100%;
        height: 50px;
    }
    .label-container {
        margin-top: 20px;
    }
</style>
