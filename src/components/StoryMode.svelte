<script>
    import ModelParams from "./ModelParams.svelte"
    import Generate from "./Generate.svelte"
    import DisplayGeneration from "./DisplayGeneration.svelte"
    import {promptPlaceholderArray} from "../utils.ts"
    import Slider from "@bulatdashiev/svelte-slider";

    export let selectedModel

    let numIterations = [200]
    let selectedResolution = [720, 1280]
    
    $: if(numIterations){
        generationParams['numIterations'] = numIterations[0]
    }

    let promptArray = ['']
    let durationArray = [[1.5]]

    let minDuration = 0.5
    let maxDuration = 10
    
    let generationParams = {
        storyGeneration: true,
        model: selectedModel.value,
        numIterations: numIterations[0],
        promptArray:promptArray,
        durationArray:durationArray,
    };
    
    let generationResultDict = {
        'imgUrl': '',
        'videoUrl': '',
    }
    
    $: genImgUrl = generationResultDict['imgUrl'];
    $: genVideoUrl = generationResultDict['videoUrl'];
    
    $: if (selectedModel.value == "aphantasia") {
        generationParams[
            "resolution"
        ] = `${selectedResolution[0]}-${selectedResolution[1]}`;
    }


    function addPrompt(){
        promptArray.push('')
        durationArray.push([durationArray[durationArray.length-1]])
        promptArray = promptArray
        durationArray = durationArray
    }

</script>

{#each promptArray as _, idx}
    <div class="input-container">
        <input
            bind:value={promptArray[idx]}
            placeholder={promptPlaceholderArray[
                Math.floor(Math.random() * promptPlaceholderArray.length)
            ]}
        />
        
        <h3>Duration {durationArray[idx][0]}</h3>
        <Slider
            bind:value={durationArray[idx]}
            min={minDuration}
            max={maxDuration}
            step="0.10"
        />

    </div>
{/each}

<button on:click={addPrompt}> Add prompt </button>

<ModelParams
    bind:selectedModel={selectedModel}
    bind:numIterations={numIterations}
    bind:selectedResolution={selectedResolution}
/>

<Generate 
    bind:generationParams={generationParams}
    bind:generationResultDict={generationResultDict}
/>

<DisplayGeneration
    bind:imgUrl={genImgUrl}
    bind:videoUrl={genVideoUrl}
/>


<style>
    .input-container {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .input-container input {
        width: 100%;
        height: 50px;
        margin-right: 20px;
    }
    .label-container {
        margin-top: 20px;
    }

</style>