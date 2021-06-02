<script>
    import ModelParams from "./ModelParams.svelte"
    import {promptPlaceholderArray} from "../utils.ts"
    import Generate from "./Generate.svelte"
    import DisplayGeneration from "./DisplayGeneration.svelte"

    export let selectedModel
 
    let numIterations = [50];
    let selectedResolution = [1024, 1024];



    let prompt = "";
    let generationResultDict = {
        'imgUrl': '',
        'videoUrl': '',
    }
    
    $: genImgUrl = generationResultDict['imgUrl'];
    $: genVideoUrl = generationResultDict['videoUrl'];

    let generationParams = {
            imageGeneration: false,
            videoGeneration: false,
            prompt: prompt,
            model: selectedModel.value,
            numIterations: numIterations[0],
        };
    
    $: if(numIterations){
        generationParams['numIterations'] = numIterations[0]
    }

    $: if (prompt){ generationParams['prompt'] = prompt }

    $: generationReady = generationParams['imageGeneration'] || generationParams['videoGeneration'];
    
    $: if (selectedModel.value == "aphantasia") {
        generationParams[
            "resolution"
        ] = `${selectedResolution[0]}-${selectedResolution[1]}`;
    }

    function updateGenerationState(generationKey) {
        generationParams[generationKey] = !generationParams[generationKey]
    }

</script>
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
            <h3>
                <input
                    type="checkbox"
                    bind:checked={generationParams["imageGeneration"]}
                    on:click={() => updateGenerationState('imageGeneration')}
                />

                Image Generation
            </h3>
        </label>
        <label>
            <h3>
                <input
                    type="checkbox"
                    bind:checked={generationParams["videoGeneration"]}
                    on:click={() => updateGenerationState('videoGeneration')}
                />
                Video Generation
            </h3>
        </label>

        <ModelParams
            selectedModel={selectedModel}
            bind:numIterations={numIterations}
            bind:selectedResolution={selectedResolution}
        />

        {#if generationReady}
            <Generate 
                bind:generationParams={generationParams}
                bind:generationResultDict={generationResultDict}
            />
        {/if}
    </div>
    
    <DisplayGeneration
        bind:imgUrl={genImgUrl}
        bind:videoUrl={genVideoUrl}
    />

{/if}

<style>
    .input-container input {
        width: 100%;
        height: 50px;
    }
    .label-container {
        margin-top: 20px;
    }
    .centered {
        display: flex;
        align-items: center;
        justify-content: center;
    }

</style>